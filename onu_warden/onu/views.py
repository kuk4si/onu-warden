import os
from django.shortcuts import render
from django.http import HttpResponseRedirect, FileResponse
from django.conf import settings
from .forms import IpForm
from .handlers import onu_warden
from pathlib import Path


def show_text_file(request):
    file_path = os.path.join(settings.BASE_DIR, 'onu', 'results', 'merged_result.txt')
    content = None
    show_content = False  # Флаг для отображения содержимого
    
    if request.method == 'POST':
        form = IpForm(request.POST)
        if form.is_valid():
            ip_address = form.cleaned_data['ip_address']
            ports = form.cleaned_data['ports']
            if form.cleaned_data['rx_threshold']:
                max_dbm = int(form.cleaned_data['rx_threshold'])
            else:
                max_dbm = None

            onu_warden(ip_address, ports, max_dbm)
            show_content = True  # Устанавливаем флаг после успешной обработки
            
            # Читаем файл только если форма валидна и была отправка
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                content = "Результаты не найдены. Файл не существует."
                
            return render(request, 'onu/optical-results.html', {
                'file_content': content,
                'form': form,
                'show_content': show_content
            })
    else:
        form = IpForm()
    
    return render(request, 'onu/optical-results.html', {
        'form': form,
        'show_content': show_content
    })


def download_file(request):
    script_dir = Path(__file__).parent.resolve()
    results_dir = script_dir / 'results'
    results_dir.mkdir(exist_ok=True)
    merged_result_path = results_dir / 'merged_result.txt'
    return FileResponse(open(merged_result_path, 'rb'), as_attachment=True)