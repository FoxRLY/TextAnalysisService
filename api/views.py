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

rabbit_host = "localhost"
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbit_host, heartbeat=900)
)

def openapi_file(request):
    return redirect("/static/docs/openapi.yaml")

def docs(request):
    # return render(request, "/static/docs/index.html")
    return redirect("/static/docs/index.html")

@method_decorator(csrf_exempt, name="dispatch")
class TextProcessingView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            text = data.get("text", "")
            theme = data.get("theme", "")

            if text and theme:
                # Запуск задачи Celery для обработки запроса
                message_id = process_analysis_request(text, theme)

                # Возвращение UUID задачи в ответе на запрос
                return JsonResponse({"uuid": str(message_id)}, status=200)
            else:
                return JsonResponse({"error": "Invalid data"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def get_processed_texts_by_id(request):
    id = request.GET.get("id", "")
    processed_texts = get_reference_samples(id=id)
    return JsonResponse(list(processed_texts), safe=False)


def get_reference_samples(id: str):
    samples = ReferenceSample.objects.filter(pk=UUID(id)).values("theme", "id", "part", "weight")
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
                    print(result)
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
