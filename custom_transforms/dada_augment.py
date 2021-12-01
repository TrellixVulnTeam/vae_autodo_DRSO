# code in this file is adpated from rpmcruz/autoaugment
# https://github.com/rpmcruz/autoaugment/blob/master/transformations.py
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import random
import PIL, PIL.ImageOps, PIL.ImageEnhance, PIL.ImageDraw
import numpy as np
import torch
from torchvision.transforms.transforms import Compose
from collections import defaultdict

__all__ = ["DadaAugment"]

random_mirror = True

def ShearX(img, v):  # [-0.3, 0.3]
    assert -0.3 <= v <= 0.3
    if random_mirror and random.random() > 0.5:
        v = -v
    return img.transform(img.size, PIL.Image.AFFINE, (1, v, 0, 0, 1, 0))


def ShearY(img, v):  # [-0.3, 0.3]
    assert -0.3 <= v <= 0.3
    if random_mirror and random.random() > 0.5:
        v = -v
    return img.transform(img.size, PIL.Image.AFFINE, (1, 0, 0, v, 1, 0))


def TranslateX(img, v):  # [-150, 150] => percentage: [-0.45, 0.45]
    assert -0.45 <= v <= 0.45
    if random_mirror and random.random() > 0.5:
        v = -v
    v = v * img.size[0]
    return img.transform(img.size, PIL.Image.AFFINE, (1, 0, v, 0, 1, 0))


def TranslateY(img, v):  # [-150, 150] => percentage: [-0.45, 0.45]
    assert -0.45 <= v <= 0.45
    if random_mirror and random.random() > 0.5:
        v = -v
    v = v * img.size[1]
    return img.transform(img.size, PIL.Image.AFFINE, (1, 0, 0, 0, 1, v))


def TranslateXAbs(img, v):  # [-150, 150] => percentage: [-0.45, 0.45]
    assert 0 <= v <= 10
    if random.random() > 0.5:
        v = -v
    return img.transform(img.size, PIL.Image.AFFINE, (1, 0, v, 0, 1, 0))


def TranslateYAbs(img, v):  # [-150, 150] => percentage: [-0.45, 0.45]
    assert 0 <= v <= 10
    if random.random() > 0.5:
        v = -v
    return img.transform(img.size, PIL.Image.AFFINE, (1, 0, 0, 0, 1, v))


def Rotate(img, v):  # [-30, 30]
    assert -30 <= v <= 30
    if random_mirror and random.random() > 0.5:
        v = -v
    return img.rotate(v)


def AutoContrast(img, _):
    return PIL.ImageOps.autocontrast(img)


def Invert(img, _):
    return PIL.ImageOps.invert(img)


def Equalize(img, _):
    return PIL.ImageOps.equalize(img)


def Flip(img, _):  # not from the paper
    return PIL.ImageOps.mirror(img)


def Solarize(img, v):  # [0, 256]
    assert 0 <= v <= 256
    return PIL.ImageOps.solarize(img, v)


def Posterize(img, v):  # [4, 8]
    assert 4 <= v <= 8
    v = int(v)
    return PIL.ImageOps.posterize(img, v)


def Posterize2(img, v):  # [0, 4]
    assert 0 <= v <= 4
    v = int(v)
    return PIL.ImageOps.posterize(img, v)


def Contrast(img, v):  # [0.1,1.9]
    assert 0.1 <= v <= 1.9
    return PIL.ImageEnhance.Contrast(img).enhance(v)


def Color(img, v):  # [0.1,1.9]
    assert 0.1 <= v <= 1.9
    return PIL.ImageEnhance.Color(img).enhance(v)


def Brightness(img, v):  # [0.1,1.9]
    assert 0.1 <= v <= 1.9
    return PIL.ImageEnhance.Brightness(img).enhance(v)


def Sharpness(img, v):  # [0.1,1.9]
    assert 0.1 <= v <= 1.9
    return PIL.ImageEnhance.Sharpness(img).enhance(v)


def Cutout(img, v):  # [0, 60] => percentage: [0, 0.2]
    assert 0.0 <= v <= 0.2
    if v <= 0.:
        return img

    v = v * img.size[0]
    return CutoutAbs(img, v)


def CutoutAbs(img, v):  # [0, 60] => percentage: [0, 0.2]
    # assert 0 <= v <= 20
    if v < 0:
        return img
    w, h = img.size
    x0 = np.random.uniform(w)
    y0 = np.random.uniform(h)

    x0 = int(max(0, x0 - v / 2.))
    y0 = int(max(0, y0 - v / 2.))
    x1 = min(w, x0 + v)
    y1 = min(h, y0 + v)

    xy = (x0, y0, x1, y1)
    color = (125, 123, 114)
    # color = (0, 0, 0)
    img = img.copy()
    PIL.ImageDraw.Draw(img).rectangle(xy, color)
    return img


def SamplePairing(imgs):  # [0, 0.4]
    def f(img1, v):
        i = np.random.choice(len(imgs))
        img2 = PIL.Image.fromarray(imgs[i])
        return PIL.Image.blend(img1, img2, v)

    return f


def augment_list(for_autoaug=True):  # 16 oeprations and their ranges
    l = [
        (ShearX, -0.3, 0.3),  # 0
        (ShearY, -0.3, 0.3),  # 1
        (TranslateX, -0.45, 0.45),  # 2
        (TranslateY, -0.45, 0.45),  # 3
        (Rotate, -30, 30),  # 4
        (AutoContrast, 0, 1),  # 5
        (Invert, 0, 1),  # 6
        (Equalize, 0, 1),  # 7
        (Solarize, 0, 256),  # 8
        (Posterize, 4, 8),  # 9
        (Contrast, 0.1, 1.9),  # 10
        (Color, 0.1, 1.9),  # 11
        (Brightness, 0.1, 1.9),  # 12
        (Sharpness, 0.1, 1.9),  # 13
        (Cutout, 0, 0.2),  # 14
        # (SamplePairing(imgs), 0, 0.4),  # 15
    ]
    if for_autoaug:
        l += [
            (CutoutAbs, 0, 20),  # compatible with auto-augment
            (Posterize2, 0, 4),  # 9
            (TranslateXAbs, 0, 10),  # 9
            (TranslateYAbs, 0, 10),  # 9
        ]
    return l


augment_dict = {fn.__name__: (fn, v1, v2) for fn, v1, v2 in augment_list()}


def get_augment(name):
    return augment_dict[name]


def apply_augment(img, name, level):
    if level < 0.0:
        level = 0.0
    elif level > 1.0:
        level = 1.0
    augment_fn, low, high = get_augment(name)
    return augment_fn(img.copy(), level * (high - low) + low)


class DadaAugment(object):
    def __init__(self, dataset):
        if dataset == 'CIFAR10':
            self.policies = dada_reduced_cifar10()
        elif dataset == 'CIFAR100':
            self.policies = dada_reduced_cifar100()
        elif dataset == 'SVHN' or dataset == 'SVHN_extra':
            self.policies = dada_reduced_svhn()
        elif dataset == 'ImageNet':
            self.policies = dada_resnet50_rimagenet()
    
    def __call__(self, img):
        for _ in range(1):
            policy = random.choice(self.policies)
            for name, pr, level in policy:
                if random.random() > pr:
                    continue
                img = apply_augment(img, name, level)
        return img


def dada_reduced_cifar10():
    p = [[('TranslateX', 0.5183464288711548, 0.5752825736999512), ('Rotate', 0.5693835616111755, 0.5274667739868164)], [('ShearX', 0.5028448104858398, 0.4595153331756592), ('Sharpness', 0.5036740303039551, 0.5378073453903198)], [('Brightness', 0.5574088096618652, 0.5563607811927795), ('Sharpness', 0.5241265296936035, 0.4670485556125641)], [('ShearY', 0.6167989373207092, 0.4837495684623718), ('Brightness', 0.4740375578403473, 0.4566589295864105)], [('ShearX', 0.4406820833683014, 0.5844581723213196), ('TranslateY', 0.3973384499549866, 0.5110136270523071)], [('Rotate', 0.39651215076446533, 0.517960250377655), ('Equalize', 0.3761792480945587, 0.36424142122268677)], [('AutoContrast', 0.4399465024471283, 0.48347008228302), ('Cutout', 0.49450358748435974, 0.5)], [('AutoContrast', 0.5601025819778442, 0.479571133852005), ('Color', 0.44876909255981445, 0.6113184690475464)], [('Rotate', 0.4231756627559662, 0.6356207132339478), ('AutoContrast', 0.59876549243927, 0.5785224437713623)], [('Invert', 0.39854735136032104, 0.5), ('Color', 0.4968028664588928, 0.4379926025867462)], [('Posterize', 0.5603401064872742, 0.49880319833755493), ('Brightness', 0.5293631553649902, 0.47918644547462463)], [('TranslateY', 0.4231869578361511, 0.5149744749069214), ('AutoContrast', 0.3750160336494446, 0.5654526352882385)], [('ShearX', 0.3773101270198822, 0.5), ('Contrast', 0.485131174325943, 0.5186365842819214)], [('ShearY', 0.5420096516609192, 0.6018360257148743), ('Rotate', 0.30701273679733276, 0.5576906800270081)], [('Posterize', 0.4173527657985687, 0.4971156716346741), ('Color', 0.450246661901474, 0.5576846599578857)], [('TranslateX', 0.4143139123916626, 0.450955331325531), ('TranslateY', 0.3599278926849365, 0.4812163710594177)], [('TranslateX', 0.574902355670929, 0.5), ('Brightness', 0.5378687381744385, 0.4751467704772949)], [('TranslateX', 0.5295567512512207, 0.5137100219726562), ('Cutout', 0.6851200461387634, 0.4909016489982605)], [('ShearX', 0.4579184353351593, 0.44350510835647583), ('Invert', 0.41791805624961853, 0.3984798192977905)], [('Rotate', 0.49958375096321106, 0.4244190752506256), ('Contrast', 0.49455592036247253, 0.4244190752506256)], [('Rotate', 0.42886781692504883, 0.46792319416999817), ('Solarize', 0.49862080812454224, 0.41575634479522705)], [('TranslateY', 0.7362872958183289, 0.5113809704780579), ('Color', 0.3918609917163849, 0.5744326114654541)], [('Equalize', 0.42245715856552124, 0.5293998718261719), ('Sharpness', 0.39708659052848816, 0.43052399158477783)], [('Solarize', 0.7260022759437561, 0.42120808362960815), ('Cutout', 0.5075806379318237, 0.46120622754096985)], [('ShearX', 0.5757555961608887, 0.563892662525177), ('TranslateX', 0.4761257469654083, 0.49035176634788513)]]
    return p

def dada_reduced_cifar100():
    p = [[('ShearY', 0.5558360815048218, 0.2755777835845947), ('Sharpness', 0.4881928265094757, 0.21691159904003143)], [('Rotate', 0.3616902828216553, 0.18580017983913422), ('Contrast', 0.5613550543785095, 0.3083491921424866)], [('TranslateY', 0.0, 0.408305287361145), ('Brightness', 0.4716355502605438, 0.5204870104789734)], [('AutoContrast', 0.7991832494735718, 0.44347289204597473), ('Color', 0.4360397756099701, 0.36640283465385437)], [('Color', 0.9439005255699158, 0.25039201974868774), ('Brightness', 0.6770737767219543, 0.44653841853141785)], [('TranslateY', 0.6285494565963745, 0.395266592502594), ('Equalize', 0.8238864541053772, 0.2982426583766937)], [('Equalize', 0.46301358938217163, 0.7147184610366821), ('Posterize', 0.5021865367889404, 0.7205064296722412)], [('Color', 0.5189914703369141, 0.482077032327652), ('Sharpness', 0.19046853482723236, 0.39753425121307373)], [('Sharpness', 0.4223572611808777, 0.37934350967407227), ('Cutout', 0.5508846044540405, 0.2419460117816925)], [('ShearX', 0.744318962097168, 0.5582589507102966), ('TranslateX', 0.4841197729110718, 0.6740695834159851)], [('Invert', 0.3582773506641388, 0.5917970538139343), ('Brightness', 0.5021751523017883, 0.2252121865749359)], [('TranslateX', 0.3551332652568817, 0.3603559732437134), ('Posterize', 0.7993623614311218, 0.3243299722671509)], [('TranslateX', 0.47883617877960205, 0.356031209230423), ('Cutout', 0.6418997049331665, 0.6689953207969666)], [('Posterize', 0.30889445543289185, 0.03791777789592743), ('Contrast', 1.0, 0.0762958824634552)], [('Contrast', 0.4202372133731842, 0.25662222504615784), ('Cutout', 0.0, 0.44168394804000854)], [('Equalize', 0.15656249225139618, 0.6881861686706543), ('Brightness', 0.72562175989151, 0.177269846200943)], [('Contrast', 0.45150792598724365, 0.33532920479774475), ('Sharpness', 0.589333176612854, 0.27893581986427307)], [('TranslateX', 0.12946638464927673, 0.5427500009536743), ('Invert', 0.3318890929222107, 0.4762207269668579)], [('Rotate', 0.4988836646080017, 0.5838819742202759), ('Posterize', 1.0, 0.7428610324859619)], [('TranslateX', 0.5078659057617188, 0.4304893910884857), ('Rotate', 0.4633696377277374, 0.48235252499580383)], [('ShearX', 0.5783067941665649, 0.455081969499588), ('TranslateY', 0.32670140266418457, 0.30824044346809387)], [('Rotate', 1.0, 0.0), ('Equalize', 0.510175883769989, 0.37381383776664734)], [('AutoContrast', 0.25783753395080566, 0.5729542374610901), ('Cutout', 0.3359143137931824, 0.34972965717315674)], [('ShearX', 0.5556561350822449, 0.5526643991470337), ('Color', 0.5021030902862549, 0.5042688846588135)], [('ShearY', 0.4626863896846771, 0.08647401630878448), ('Posterize', 0.5513173341751099, 0.3414877951145172)]]
    return p

def dada_reduced_svhn():
    p = [[('Solarize', 0.6144442558288574, 0.5266356468200684), ('Brightness', 0.6407432556152344, 0.49594756960868835)], [('ShearY', 0.5603815317153931, 0.5412482619285583), ('Sharpness', 0.6651169061660767, 0.5049636363983154)], [('AutoContrast', 0.6381033658981323, 0.4964789152145386), ('Posterize', 0.48855721950531006, 0.422171413898468)], [('Invert', 0.43413209915161133, 0.6199576258659363), ('Equalize', 0.29578277468681335, 0.5297484397888184)], [('Contrast', 0.4938320219516754, 0.5492982864379883), ('Color', 0.5132512450218201, 0.5783136487007141)], [('ShearX', 0.5763686299324036, 0.5030161142349243), ('Brightness', 0.5642024278640747, 0.5401291847229004)], [('Rotate', 0.42828381061553955, 0.5006870627403259), ('Contrast', 0.4703759551048279, 0.42430493235588074)], [('Brightness', 0.510947048664093, 0.5679713487625122), ('Cutout', 0.4846647381782532, 0.5044050216674805)], [('TranslateY', 0.6543954610824585, 0.46405279636383057), ('Rotate', 0.4259282052516937, 0.46405279636383057)], [('ShearY', 0.4125938415527344, 0.42883598804473877), ('Contrast', 0.4826575219631195, 0.4939113259315491)], [('ShearY', 0.5181029438972473, 0.37303897738456726), ('Brightness', 0.4268920421600342, 0.37303897738456726)], [('ShearY', 0.2554332911968231, 0.488460898399353), ('Posterize', 0.5154975652694702, 0.5595977902412415)], [('TranslateX', 0.6652320623397827, 0.3767608106136322), ('TranslateY', 0.4480351507663727, 0.42192813754081726)], [('Posterize', 0.6448476314544678, 0.4292587637901306), ('Sharpness', 0.6318501830101013, 0.5380985140800476)], [('Rotate', 0.47309818863868713, 0.5), ('Sharpness', 0.40288078784942627, 0.4530191421508789)], [('ShearX', 0.46573129296302795, 0.4571962058544159), ('Cutout', 0.5832347869873047, 0.5)], [('Rotate', 0.5847659111022949, 0.5309413075447083), ('Solarize', 0.4149461090564728, 0.4334002733230591)], [('Color', 0.36979031562805176, 0.4367675483226776), ('Brightness', 0.5150350332260132, 0.4127320945262909)], [('TranslateX', 0.49473315477371216, 0.46626225113868713), ('Posterize', 0.4864722192287445, 0.5235840082168579)], [('TranslateY', 0.5033610463142395, 0.4902884066104889), ('Solarize', 0.4999811351299286, 0.420960932970047)], [('TranslateY', 0.265391081571579, 0.5), ('Invert', 0.5603448748588562, 0.29043102264404297)], [('ShearY', 0.636258065700531, 0.5717220902442932), ('Rotate', 0.48708420991897583, 0.5717220902442932)], [('Invert', 0.48760682344436646, 0.5459234118461609), ('Contrast', 0.40973231196403503, 0.5)], [('ShearX', 0.5675588250160217, 0.48917657136917114), ('Color', 0.6019042134284973, 0.5)], [('Rotate', 0.5409624576568604, 0.5262851119041443), ('Equalize', 0.5241876244544983, 0.5)]]
    return p

def dada_resnet50_rimagenet():
    p = [[('TranslateY', 0.8485236167907715, 0.6384843587875366), ('Contrast', 0.6994985342025757, 0.4658013582229614)], [('ShearX', 0.6867295503616333, 0.6413730978965759), ('Brightness', 0.5846965312957764, 0.4594041705131531)], [('Solarize', 0.32854214310646057, 0.5276699066162109), ('Contrast', 0.35618481040000916, 0.40267977118492126)], [('ShearY', 0.5445513129234314, 0.8130137920379639), ('Color', 0.6470239162445068, 0.6705710291862488)], [('Rotate', 0.5192075371742249, 0.2825779616832733), ('Invert', 0.550243616104126, 0.4626586139202118)], [('ShearY', 0.7560662031173706, 0.5509522557258606), ('AutoContrast', 0.6409668922424316, 0.4606546461582184)], [('TranslateX', 0.31624406576156616, 0.6743366122245789), ('Sharpness', 0.4453914165496826, 0.6102295517921448)], [('Brightness', 0.2804577350616455, 0.5395416021347046), ('Cutout', 0.292346328496933, 0.5346128344535828)], [('TranslateY', 0.26140129566192627, 0.3906748592853546), ('Brightness', 0.30170461535453796, 0.5674546360969543)], [('ShearX', 0.46454519033432007, 0.621078610420227), ('Rotate', 0.5081079006195068, 0.585682213306427)], [('TranslateY', 0.6333466172218323, 0.3763497471809387), ('Invert', 0.39652955532073975, 0.3273072838783264)], [('TranslateY', 0.49120470881462097, 0.3186573386192322), ('Equalize', 0.42822957038879395, 0.26451754570007324)], [('TranslateX', 0.3068506419658661, 0.46462544798851013), ('AutoContrast', 0.40107735991477966, 0.0)], [('ShearY', 0.574976921081543, 0.34980109333992004), ('Equalize', 0.4476233124732971, 0.16299982368946075)], [('Solarize', 0.7755236029624939, 0.6112682223320007), ('Brightness', 0.5702967047691345, 0.7999937534332275)], [('Color', 0.7510525584220886, 0.404958575963974), ('Cutout', 0.5368577837944031, 0.4658619165420532)], [('ShearX', 0.5083368420600891, 0.6662658452987671), ('Cutout', 0.36978110671043396, 0.4463765323162079)], [('TranslateX', 0.6763074994087219, 0.38640040159225464), ('Rotate', 0.4725652039051056, 0.163239985704422)], [('Rotate', 0.643989086151123, 0.5495110750198364), ('Sharpness', 0.6552684307098389, 0.7961348295211792)], [('TranslateY', 0.4652615785598755, 0.748457670211792), ('Sharpness', 0.6427830457687378, 0.5193099975585938)], [('AutoContrast', 0.2942410111427307, 0.5420864820480347), ('Posterize', 0.35267922282218933, 0.6994035243988037)], [('Invert', 0.5537762641906738, 0.48860815167427063), ('Equalize', 0.444082111120224, 0.7564548254013062)], [('TranslateX', 0.857695996761322, 0.2923051416873932), ('Contrast', 0.40830710530281067, 0.6012328267097473)], [('Invert', 0.27794185280799866, 0.4498332142829895), ('Posterize', 0.422256737947464, 0.336642324924469)], [('Posterize', 0.1463455855846405, 0.3278478980064392), ('Color', 0.49619558453559875, 0.5923987030982971)]]
    return p

