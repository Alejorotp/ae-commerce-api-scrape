import replicate
import time

MODEL_VERSION = "subhash25rawat/flux-vton:a02643ce418c0e12bad371c4adbfaec0dd1cb34b034ef37650ef205f92ad6199"
NANO_BANANA_MODEL = "google/nano-banana-2"

def generate_tryon_flux(person_image_url, garment_url):
    print("Starting VTON generation...")
    input_data = {
        "part": "upper_body",
        "image": person_image_url,
        "garment": garment_url
    }
    print("Input data created")
    print(input_data)
    
    start_time = time.time()

    output = replicate.run(
        MODEL_VERSION,
        input=input_data
    )
    end_time = time.time()

    print("Replicate finished")
    print(f"Execution time: {end_time - start_time} seconds")

    print("Output:")
    print(output)

    return output.url


def generate_tryon_nano(person_image_url, garment_url):

    print("Starting Nano Banana generation...")

    prompt = f"""
    The first image is a person.
    The second image is a clothing item.

    Dress the person using the clothing from the second image.

    Keep the same person identity and facial features.
    Do not change the pose or background.
    
    Make the clothing realistic and natural.
    """

    input_data = {
        "prompt": prompt,
        "image_input": [
            person_image_url,
            garment_url
        ],
        "resolution": "1K",
        "aspect_ratio": "match_input_image",
        "output_format": "jpg"
    }

    start_time = time.time()

    output = replicate.run(
        NANO_BANANA_MODEL,
        input=input_data
    )

    end_time = time.time()

    print(f"Nano Banana execution time: {end_time - start_time} seconds")

    print(output)
    
    return output.url