# custom_imports = dict(imports=['tools/misc/custom_optimizer.py', 'tools/misc/one_cycle_lr_update.py'])

_base_ = [
    '../_base_/default_runtime.py'
]

# model settings
model = dict(
    type='YOLOV5',
    backbone=dict(type='YOLOV5Backbone', depth_multiple=0.33, width_multiple=0.5),
    neck=None,
    bbox_head=dict(
        type='YOLOV5Head',
        num_classes=80,
        in_channels=[512, 256, 128],
        out_channels=[0.33, 0.5, 1],
        anchor_generator=dict(
            type='YOLOAnchorGenerator',
            base_sizes=[[(116, 90), (156, 198), (373, 326)],
                        [(30, 61), (62, 45), (59, 119)],
                        [(10, 13), (16, 30), (33, 23)]],
            strides=[32, 16, 8]),
        bbox_coder=dict(type='YOLOV5BBoxCoder'),
        featmap_strides=[32, 16, 8],
        loss_cls=dict(
            type='CrossEntropyLoss',
            use_sigmoid=True,
            loss_weight=1.0,
            reduction='sum'),
        loss_conf=dict(
            type='CrossEntropyLoss',
            use_sigmoid=True,
            loss_weight=1.0,
            reduction='sum'),
        loss_xy=dict(
            type='CrossEntropyLoss',
            use_sigmoid=True,
            loss_weight=2.0,
            reduction='sum'),
        loss_wh=dict(type='MSELoss', loss_weight=2.0, reduction='sum')
    ),
    test_cfg=dict(
        use_v3=False,  # 是否使用 mmdet v3 原本的后处理策略
        score_thr=0.05,  # 仅仅当 use_v3 为 True 才有效
        nms_pre=1000,  # 仅仅当 use_v3 为 True 才有效
        agnostic=False,  # 是否区分类别进行 nms，False 表示要区分
        multi_label=True,  # 是否考虑多标签， 单张图检测是为 False，test 时候为 True，可以提高 1 个点的 mAP
        min_bbox_size=0,
        # detect: conf_thr=0.25 iou_threshold=0.45
        # test: conf_thr=0.001 iou_threshold=0.65
        conf_thr=0.001,
        nms=dict(type='nms', iou_threshold=0.65),
        max_per_img=300)
)

img_norm_cfg = dict(mean=[0., 0., 0.], std=[255., 255., 255.], to_rgb=True)

# dataset settings
dataset_type = 'YOLOV5CocoDataset'
# data_root = '/home/PJLAB/huanghaian/dataset/coco/'
data_root = 'data/coco/'

train_pipeline = [
    dict(type='Normalize', **img_norm_cfg),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels'],
         meta_keys=('img_norm_cfg',)),
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(640, 640),
        flip=False,
        transforms=[
            # dict(type='ShapeLetterResize', img_scale=(640, 640), scaleup=True, auto=False),  # test
            dict(type='ShapeLetterResize', img_scale=(640, 640), scaleup=False, auto=False, with_yolov5=True),  #  test，和原始v5完全一致的写法
            # dict(type='LetterResize', img_scale=(640, 640), scaleup=True, auto=True),  # detect
            dict(type='RandomFlip'),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='Pad', size_divisor=32),
            dict(type='DefaultFormatBundle'),
            dict(type='Collect', keys=['img'],
                 meta_keys=('filename', 'ori_filename', 'ori_shape',
                            'img_shape', 'pad_shape', 'scale_factor', 'flip',
                            'flip_direction', 'img_norm_cfg', 'pad_param'))
        ])
]

repeat_num = 3
max_epoch = 300 // 3

data = dict(
    samples_per_gpu=16,  # total=64 8gpu
    workers_per_gpu=4,
    train=dict(
        _delete_=True,
        type='RepeatDataset',
        times=repeat_num,
        dataset=dict(
            type=dataset_type,
            ann_file=data_root + 'annotations/instances_val2017.json',
            img_prefix=data_root + 'val2017/',
            pipeline=train_pipeline)),
    # train=dict(
    #     type=dataset_type,
    #     ann_file=data_root + 'annotations/instances_val2017.json',
    #     img_prefix=data_root + 'val2017/',
    #     pipeline=train_pipeline),
    val=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/instances_val2017.json',
        img_prefix=data_root + 'val2017/',
        pipeline=test_pipeline),
    test=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/instances_val2017.json',
        img_prefix=data_root + 'val2017/',
        pipeline=test_pipeline))

evaluation = dict(interval=5, metric='bbox')
checkpoint_config = dict(interval=5)

# optimizer
optimizer = dict(constructor='CustomOptimizer', type='SGD', lr=0.01, momentum=0.937, nesterov=True)
optimizer_config = dict(grad_clip=dict(max_norm=35, norm_type=2))

# learning policy
lr_config = dict(policy='OneCycle', repeat_num=repeat_num, max_epoch=max_epoch)
runner = dict(type='EpochBasedRunner', max_epochs=max_epoch)

log_config = dict(interval=30)

custom_hooks = [dict(type='EMAHook', priority=49)]

# 注意：暂时 fp16 和 AccumulateOptimizerHook 不兼容，只能开一个
# 如果你总 batch大于等于 64，那么不需要 AccumulateOptimizerHook，可以开启 fp16
# 如果你想使用梯度累积，那么就需要注释 fp16 配置
# 如果 batch 大于等于64，并且显卡不支持fp16，那么全部注释即可


# fp16 settings
# fp16 = dict(loss_scale='dynamic')


# std_batch = 64
# total_batch = 16
# optimizer_config = dict(type="AccumulateOptimizerHook",
#                         grad_clip=dict(max_norm=35, norm_type=2),
#                         update_iterval=int(std_batch / total_batch),
#                         repeat_num=repeat_num)
