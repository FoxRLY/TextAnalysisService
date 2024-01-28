from os import stat
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import uuid
import pika
from .models import ReferenceSample, UploadedFile
from .forms import UploadFileForm
from uuid import UUID
from django.shortcuts import redirect
from asyncio import sleep, CancelledError

rabbit_host = "rabbit"
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbit_host, heartbeat=900)
)

def openapi_file(request):
    return redirect("/static/docs/openapi.yaml")

def docs(request):
    return redirect("/static/docs/index.html")

@method_decorator(csrf_exempt, name="dispatch")
class TextProcessingView(View):
    async def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            results = await process_texts(data)
            return JsonResponse(results)
        except CancelledError as e:
            print("Response cancelled")
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


async def process_texts(data):
    result = dict()
    texts = []
    if isinstance(data, list):
        texts = data
    elif isinstance(data, dict):
        texts = [data]
    if not (all([text.get("text") != None for text in texts]) and all([text.get("theme") != None for text in texts])):
        raise ValueError("Wrong JSON format")

    text_ids = [process_analysis_request(text.get("text"), text.get("theme")) for text in texts]
    for id in text_ids:
        while True:
            if len(samples := await get_reference_samples(id)) > 0:
                result[id] = samples
                break
            await sleep(1)
    return result


async def get_processed_texts_by_id(request):
    id = request.GET.get("id", "")
    processed_texts =  await get_reference_samples(id=id)
    return JsonResponse(list(processed_texts), safe=False)


async def get_reference_samples(id: str):
    samples = []
    async for entry in ReferenceSample.objects.filter(pk=UUID(id)).values("theme", "part", "weight"):
        entry["weight"] = round(entry["weight"] * 10)
        if entry["weight"] < 1:
            entry["weight"] = 1
        samples.append(entry)
    # print(samples)
    return samples


def process_analysis_request(text, theme):
    message_id = str(uuid.uuid4())
    data = [
        {
            "id": message_id,
            "text": text,
            "theme": theme,
            "label": "?",
        }
    ]

    channel = connection.channel()
    queue = channel.queue_declare("texts_analysis")
    queue_name = queue.method.queue

    channel.basic_publish(
        exchange="",
        body=json.dumps(data, ensure_ascii=False),
        routing_key=queue_name,
    )

    return message_id


def upload_reference_samples(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            channel = connection.channel()
            queue = channel.queue_declare("texts_analysis")
            queue_name = queue.method.queue
            file = UploadedFile(file=request.FILES["file"]).file
            data = json.load(file)
            for item in data:
                for answer_item in item.get("answers", []):
                    id = str(uuid.uuid4())
                    text = answer_item
                    label = "1"
                    theme = item.get("id")

                    result = [{"id": id, "text": text, "label": label, "theme": theme}]
                    # print(result)
                    # Отправка результата в брокер
                    channel.basic_publish(
                        exchange="",
                        body=json.dumps(result, ensure_ascii=False),
                        routing_key=queue_name,
                    )
            return HttpResponseRedirect("/upload-success")
    else:
        form = UploadFileForm()
    return render(request, "upload.html", {"form": form})


def upload_success(request):
    return HttpResponse("Загрузка прошла успешно")
