from diffusers import DDIMScheduler

from deps.AnimateDiff.animatediff.pipelines.pipeline_animation import AnimationPipeline
import deps.AnimateDiff.animatediff.utils.convert_from_ckpt as cvt
import modules.diffusion_model as dm
import modules.motion_module as mm
import modules.stable_diffusion as sd


def create_animation_pipeline():
    print('Creating animation pipeline...')
    pipeline = AnimationPipeline(
        text_encoder=sd.load_text_encoder(),
        tokenizer=sd.load_tokenizer(),
        vae=sd.load_vae(),
        unet=sd.load_unet(),
        scheduler=DDIMScheduler(**{
            'num_train_timesteps': 1000,
            'beta_start': 0.00085,
            'beta_end': 0.012,
            'beta_schedule': 'linear',
            'steps_offset': 1,
            'clip_sample': False
        }),
    )

    pipeline.to("cuda")

    print('Loading motion module to the animation pipeline...')
    _, unexpected = pipeline.unet.load_state_dict(mm.load_state_dict(), strict=False)
    if len(unexpected) > 0:
        exit('Failed to load motion module to the animation pipeline!')

    print('Loading diffusion model to the animation pipeline...')
    state_dict = dm.load_model()

    converted_vae_checkpoint = cvt.convert_ldm_vae_checkpoint(state_dict, pipeline.vae.config)
    pipeline.vae.load_state_dict(converted_vae_checkpoint)

    converted_unet_checkpoint = cvt.convert_ldm_unet_checkpoint(state_dict, pipeline.unet.config)
    pipeline.unet.load_state_dict(converted_unet_checkpoint, strict=False)

    pipeline.text_encoder = cvt.convert_ldm_clip_checkpoint(state_dict)

    pipeline.to("cuda")

    return pipeline