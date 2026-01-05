import traceback
from google import genai
from google.genai import types
from io import BytesIO
from PIL import Image
from src.services.utils.gcp_upload_service import uploadDoc

IMAGEN_MODELS = {
    "imagen-4.0-generate-001",
    "imagen-4.0-ultra-generate-001",
    "imagen-4.0-fast-generate-001",
    "imagen-4.0-generate-preview-06-06",
    
}

async def gemini_image_model(configuration, apikey, execution_time_logs, timer):
    try:
        client = genai.Client(api_key=apikey)

        prompt = configuration.pop("prompt", "")
        model = configuration.pop("model")

        timer.start()

        # ----------------------------------
        # IMAGEN MODELS
        # ----------------------------------
        if model in IMAGEN_MODELS:
            response = client.models.generate_images(
                model=model,
                prompt=prompt,
                config=types.GenerateImagesConfig(**configuration) if configuration else None
            )

            execution_time_logs.append({
                "step": "Imagen image Processing time",
                "time_taken": timer.stop("Imagen image Processing time")
            })

            gcp_urls = []

            for img in response.generated_images:
                image = Image.open(BytesIO(img.image.image_bytes))

                img_buffer = BytesIO()
                image.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                gcp_url = await uploadDoc(
                    file=img_buffer,
                    folder="generated-images",
                    real_time=True,
                    content_type="image/png"
                )

                gcp_urls.append(gcp_url)

            return {
                "success": True,
                "response": {
                    "data": [
                        {
                            "urls": gcp_urls,
                            "text_content": []
                        }
                    ]
                }
            }

        else:
            aspect_ratio = configuration.pop('aspect_ratio', None)
            image_size = configuration.pop('image_size', None)
            print(model, aspect_ratio, image_size)
        # Build the configuration
            config_params = {
                'response_modalities': ['TEXT', 'IMAGE']
            }
        
       
            config_params['image_config'] = types.ImageConfig(aspect_ratio=aspect_ratio, image_size=image_size)

        # Add any remaining configuration parameters
            for key, value in configuration.items():
                config_params[key] = value

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_params)
            )

            execution_time_logs.append({
            "step": "Gemini image Processing time",
            "time_taken": timer.stop("Gemini image Processing time")
            })

            text_content = []
            gcp_url = None

            for part in response.candidates[0].content.parts:
                if part.text:
                    text_content.append(part.text)

                elif part.inline_data:
                    image = Image.open(BytesIO(part.inline_data.data))

                    img_buffer = BytesIO()
                    image.save(img_buffer, format="PNG")
                    img_buffer.seek(0)

                    gcp_url = await uploadDoc(
                        file=img_buffer,
                        folder="generated-images",
                        real_time=True,
                        content_type="image/png"
                    )

            return {
                "success": True,
                "response": {
                    "data": [
                        {
                            "url": gcp_url,
                            "text_content": text_content
                        }
                    ]
                }
            }
        

    except Exception as error:
        execution_time_logs.append({
            "step": "Image Processing time",
            "time_taken": timer.stop("Image Processing time")
        })
        traceback.print_exc()

        return {
            "success": False,
            "error": str(error)
        }
