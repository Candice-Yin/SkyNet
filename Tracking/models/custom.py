import sys, os
sys.path.append(os.pardir)
sys.path.append("/home/max/work/SkyNet/Tracking/models")
from siammask import SiamMask
from features import MultiStageFeature
from rpn import RPN, DepthCorr
from mask import Mask

import torch
import torch.nn as nn

sys.path.append("/home/max/work/SkyNet/Tracking/utils")
from load_helper import load_pretrain


#from .resnet import resnet50
#from .skynet import SkyNet
from resnet import resnet50
from skynet import SkyNet



class ResDownS(nn.Module):
    def __init__(self, inplane, outplane):
        super(ResDownS, self).__init__()
        self.downsample = nn.Sequential(
                nn.Conv2d(inplane, outplane, kernel_size=1, bias=False),
                nn.BatchNorm2d(outplane))

    def forward(self, x):
        x = self.downsample(x)
        if x.size(3) < 20:
            l = 4
            r = -4
            x = x[:, :, l:r, l:r]
        return x


class ResDown(MultiStageFeature):
    def __init__(self, model):
        super(ResDown, self).__init__()
        if model is SkyNet:
            self.backbone = 'Sky'
            self.features = model()
            self.downsample = ResDownS(1000, 256)
            self.layers = [self.downsample, self.features]
            self.train_nums = [1, 2]
        else:
            self.backbone = 'resnet'
            self.features = model(layer3=True, layer4=False)
            self.downsample = ResDownS(1024, 256)
            self.layers = [self.downsample, self.features.layer2, self.features.layer3]
            self.train_nums = [1, 3]

        self.change_point = [0, 0.5]
        self.unfix(0.0)

    def param_groups(self, start_lr, feature_mult=1):
        lr = start_lr * feature_mult

        def _params(module, mult=1):
            params = list(filter(lambda x:x.requires_grad, module.parameters()))
            if len(params):
                return [{'params': params, 'lr': lr * mult}]
            else:
                return []

        groups = []
        groups += _params(self.downsample)
        groups += _params(self.features, 0.1)
        return groups

    def forward(self, x):
        output = self.features(x)
        # print(output)
        if self.backbone == 'resnet':
            p3 = self.downsample(output[1])
        else:
            # output = output.permute(0, 2, 3, 1)
            p3 = self.downsample(output)
        return p3


class UP(RPN):
    def __init__(self, anchor_num=5, feature_in=256, feature_out=256):
        super(UP, self).__init__()

        self.anchor_num = anchor_num
        self.feature_in = feature_in
        self.feature_out = feature_out

        self.cls_output = 2 * self.anchor_num
        self.loc_output = 4 * self.anchor_num

        self.cls = DepthCorr(feature_in, feature_out, self.cls_output)
        self.loc = DepthCorr(feature_in, feature_out, self.loc_output)

    def forward(self, z_f, x_f):
        cls = self.cls(z_f, x_f)
        loc = self.loc(z_f, x_f)
        return cls, loc


class MaskCorr(Mask):
    def __init__(self, oSz=63):
        super(MaskCorr, self).__init__()
        self.oSz = oSz
        self.mask = DepthCorr(256, 256, self.oSz**2)

    def forward(self, z, x):
        return self.mask(z, x)


class Custom_Sky(SiamMask):
    def __init__(self, pretrain=False, **kwargs):
        super().__init__(**kwargs)
        self.features = ResDown(SkyNet)
        self.rpn_model = UP(anchor_num=self.anchor_num, feature_in=256, feature_out=256)
        self.mask_model = MaskCorr()

    def template(self, template):
        self.zf = self.features(template)

    def track(self, search):
        search = self.features(search)
        rpn_pred_cls, rpn_pred_loc = self.rpn(self.zf, search)
        return rpn_pred_cls, rpn_pred_loc

    def track_mask(self, search):
        search = self.features(search)
        rpn_pred_cls, rpn_pred_loc = self.rpn(self.zf, search)
        pred_mask = self.mask(self.zf, search)
        return rpn_pred_cls, rpn_pred_loc, pred_mask


class Custom(SiamMask):
    def __init__(self, pretrain=False, **kwargs):
        super().__init__(**kwargs)
        self.features = ResDown(resnet50)
        self.rpn_model = UP(anchor_num=self.anchor_num, feature_in=256, feature_out=256)
        self.mask_model = MaskCorr()

    def template(self, template):
        self.zf = self.features(template)

    def track(self, search):
        search = self.features(search)
        rpn_pred_cls, rpn_pred_loc = self.rpn(self.zf, search)
        return rpn_pred_cls, rpn_pred_loc

    def track_mask(self, search):
        search = self.features(search)
        rpn_pred_cls, rpn_pred_loc = self.rpn(self.zf, search)
        pred_mask = self.mask(self.zf, search)
        return rpn_pred_cls, rpn_pred_loc, pred_mask

