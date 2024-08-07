from selfweed.detector import HoughCropRowDetector, get_vegetation_detector
from selfweed.models.pseudo import PseudoModel
from selfweed.models.rowweeder import RowWeeder

from transformers.models.segformer.modeling_segformer import SegformerForImageClassification, SegformerConfig, SegformerForSemanticSegmentation
from transformers import ResNetForImageClassification, SwinModel, SwinConfig

from selfweed.models.segmentation import HoughCC, HoughSLIC, HoughSLICSegmentationWrapper
from selfweed.models.utils import HuggingFaceClassificationWrapper, HuggingFaceWrapper
from selfweed.models.pyramid import MLFormer, PyramidFormer
from selfweed.data.weedmap import WeedMapDataset, ClassificationWeedMapDataset

def build_rowweeder_model(
    encoder,
    input_channels,
    embedding_size,
    embedding_dims,
    transformer_layers=4
):
    
    return RowWeeder(
        encoder,
        input_channels=input_channels,
        embedding_size=embedding_size,
        embedding_dims=embedding_dims,
        transformer_layers=transformer_layers,
    )
    

def build_roweeder_segformer(
    input_channels,
    transformer_layers=4,
    embedding_size=(1, ),
    version="nvidia/mit-b0"
):
    encoder = SegformerForImageClassification.from_pretrained(version)
    embeddings_dims = SegformerConfig.from_pretrained(version).hidden_sizes
    encoder = encoder.segformer.encoder
    return build_rowweeder_model(encoder, input_channels, embedding_size, embeddings_dims, transformer_layers)


def build_pyramidformer(
    input_channels,
    version="nvidia/mit-b0",
    fusion="concat",
    upsampling="interpolate",
    blocks=4,
    spatial_conv=True,
):
    encoder = SegformerForImageClassification.from_pretrained(version)
    embeddings_dims = SegformerConfig.from_pretrained(version).hidden_sizes
    embeddings_dims = embeddings_dims[:blocks]
    num_classes = len(WeedMapDataset.id2class)
    return PyramidFormer(encoder, embeddings_dims, num_classes, fusion=fusion, upsampling=upsampling, blocks=blocks, spatial_conv=spatial_conv)


def build_mlformer(
    input_channels,
    version="nvidia/mit-b0",
    fusion="concat",
    upsampling="interpolate",
    spatial_conv=True,
    blocks=4
):
    encoder = SegformerForImageClassification.from_pretrained(version)
    embeddings_dims = SegformerConfig.from_pretrained(version).hidden_sizes
    embeddings_dims = embeddings_dims[:blocks]
    num_classes = len(WeedMapDataset.id2class)
    return MLFormer(encoder, embeddings_dims, num_classes, fusion=fusion, upsampling=upsampling, spatial_conv=spatial_conv)


def build_segformer(
    input_channels,
    version="nvidia/mit-b0"
):
    segformer = SegformerForSemanticSegmentation.from_pretrained(
        version,
        id2label=WeedMapDataset.id2class,
        label2id={v: k for k,v in WeedMapDataset.id2class.items()}
        )
    return HuggingFaceWrapper(segformer)


def build_swinmlformer(
    input_channels,
    version="microsoft/swin-tiny-patch4-window7-224",
    fusion="concat",
    upsampling="interpolate",
    spatial_conv=True,
    blocks=5,
):
    encoder = SwinModel.from_pretrained(version)
    config = SwinConfig.from_pretrained(version)
    emb_range = min(blocks, 4)
    embeddings_dims = [config.embed_dim * (2**i) for i in range(emb_range)]
    if blocks > 4:
        embeddings_dims += embeddings_dims[-1:]
    embeddings_dims = embeddings_dims[:blocks]
    scale_factors = [2, 4, 8, 8][:blocks]
    num_classes = len(WeedMapDataset.id2class)
    return MLFormer(encoder, embeddings_dims, num_classes, fusion=fusion, upsampling=upsampling, spatial_conv=spatial_conv, scale_factors=scale_factors)


def build_resnet50(
    input_channels,
    plant_detector_params,
    slic_params,
    internal_batch_size=1,
):
    classification_model = HuggingFaceClassificationWrapper(ResNetForImageClassification.from_pretrained(
        "microsoft/resnet-50",
        id2label=ClassificationWeedMapDataset.id2class,
        label2id={v: k for k,v in ClassificationWeedMapDataset.id2class.items()},
        ignore_mismatched_sizes=True,
        ))
    plant_detector = get_vegetation_detector(
        plant_detector_params["name"], plant_detector_params["params"]
    )
    return HoughSLICSegmentationWrapper(classification_model, plant_detector, slic_params, internal_batch_size=internal_batch_size)


def build_houghcc(
    input_channels,
    plant_detector_params,
    hough_detector_params,
):
    plant_detector = get_vegetation_detector(
        plant_detector_params["name"], plant_detector_params["params"]
    )
    hough_detector = HoughCropRowDetector(**hough_detector_params)
    return HoughCC(plant_detector=plant_detector, hough_detector=hough_detector)


def build_houghslic(
    input_channels,
    plant_detector_params,
    hough_detector_params,
    slic_params,
):
    plant_detector = get_vegetation_detector(
        plant_detector_params["name"], plant_detector_params["params"]
    )
    hough_detector = HoughCropRowDetector(**hough_detector_params)
    return HoughSLIC(plant_detector=plant_detector, hough_detector=hough_detector, slic_params=slic_params)

def build_pseudo_gt_model(
    gt_folder
):
    return PseudoModel(gt_folder)
