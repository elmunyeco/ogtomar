from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
# earthbox/views.py
def home(request):
    # una vista simple con template (si querés)
    return render(request, 'earthbox/home.html', {'msg': 'Hola desde earthbox 👋'})

def echo(request):
    # te devuelve lo que le mandes por ?q=
    q = request.GET.get('q', '')
    return HttpResponse(f"Echo: {q}")
