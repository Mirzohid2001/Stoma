from datetime import datetime
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models import Client, Order, Payment


def _parse_date(s):
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


@login_required
def export_sales_excel(request):
    from_date = _parse_date(request.GET.get('from')) or (timezone.now().date() - __import__('datetime').timedelta(days=30))
    to_date = _parse_date(request.GET.get('to')) or timezone.now().date()

    payments = Payment.objects.filter(
        payment_date__gte=from_date,
        payment_date__lte=to_date
    ).select_related('order', 'order__client').order_by('payment_date')

    wb = Workbook()
    ws = wb.active
    ws.title = 'Savdo hisoboti'
    ws.append(['Sana', 'Mijoz', 'Buyurtma', 'Summa (so\'m)'])
    for p in payments:
        ws.append([str(p.payment_date), p.order.client.full_name, p.order.order_number, float(p.amount)])
    total = payments.aggregate(s=Sum('amount'))['s'] or 0
    ws.append(['', '', 'Jami', float(total)])

    resp = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = f'attachment; filename=savdo_{from_date}_{to_date}.xlsx'
    wb.save(resp)
    return resp


@login_required
def export_sales_pdf(request):
    from_date = _parse_date(request.GET.get('from')) or (timezone.now().date() - __import__('datetime').timedelta(days=30))
    to_date = _parse_date(request.GET.get('to')) or timezone.now().date()

    payments = list(Payment.objects.filter(
        payment_date__gte=from_date,
        payment_date__lte=to_date
    ).select_related('order', 'order__client').order_by('payment_date'))

    total = sum(float(p.amount) for p in payments)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph('Savdo hisoboti', styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f'Sana: {from_date} — {to_date}', styles['Normal']))
    elements.append(Spacer(1, 20))

    data = [['Sana', 'Mijoz', 'Buyurtma', 'Summa']]
    for p in payments[:100]:
        data.append([str(p.payment_date), p.order.client.full_name[:30], p.order.order_number, f'{float(p.amount):,.0f}'])
    if len(payments) > 100:
        data.append(['...', f'{len(payments)-100} ta yana', '', ''])
    data.append(['', '', 'Jami', f'{total:,.0f} so\'m'])

    t = Table(data, colWidths=[60, 120, 80, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
    ]))
    elements.append(t)
    doc.build(elements)

    resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename=savdo_{from_date}_{to_date}.pdf'
    return resp


@login_required
def export_debts_excel(request):
    today = timezone.now().date()
    debtors = []
    seen = set()
    for order in Order.objects.filter(status__in=['draft', 'in_progress']).select_related('client'):
        if order.remaining_debt <= 0 or order.client_id in seen:
            continue
        seen.add(order.client_id)
        dl = order.debt_payment_deadline
        debtors.append({
            'client': order.client,
            'debt': order.client.total_debt,
            'deadline': dl,
            'days_left': (dl - today).days if dl else None,
        })

    wb = Workbook()
    ws = wb.active
    ws.title = 'Qarzdorlar'
    ws.append(['Mijoz', 'Telefon', 'Qarz (so\'m)', 'To\'lov sanasi', 'Qolgan kun'])
    for d in debtors:
        ws.append([
            d['client'].full_name,
            d['client'].phone,
            float(d['debt']),
            str(d['deadline']) if d['deadline'] else '',
            d['days_left'] if d['days_left'] is not None else '',
        ])

    resp = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = 'attachment; filename=qarzdorlar.xlsx'
    wb.save(resp)
    return resp


@login_required
def export_debts_pdf(request):
    today = timezone.now().date()
    debtors = []
    seen = set()
    for order in Order.objects.filter(status__in=['draft', 'in_progress']).select_related('client'):
        if order.remaining_debt <= 0 or order.client_id in seen:
            continue
        seen.add(order.client_id)
        dl = order.debt_payment_deadline
        days_left = (dl - today).days if dl else None
        debtors.append({
            'client': order.client,
            'debt': float(order.client.total_debt),
            'deadline': str(dl) if dl else '—',
            'days_left': str(days_left) if days_left is not None else '—',
        })

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph('Qarzdorlar hisoboti', styles['Title']))
    elements.append(Spacer(1, 20))

    data = [['Mijoz', 'Telefon', 'Qarz', "To'lov sanasi", 'Kun']]
    for d in debtors:
        data.append([d['client'].full_name[:25], d['client'].phone[:15], f"{d['debt']:,.0f}", d['deadline'], d['days_left']])

    t = Table(data, colWidths=[100, 80, 80, 80, 50])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(t)
    doc.build(elements)

    resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename=qarzdorlar.pdf'
    return resp
