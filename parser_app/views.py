from django.shortcuts import render
from django.http import HttpResponse


def main(request):
    return render(request, 'parser_app/main.html', {})
# Create your views here.
