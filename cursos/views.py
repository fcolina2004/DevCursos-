from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .forms import RegistroForm 
from .models import Curso, Estudiante, Inscripcion, Horario

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST) 
        if form.is_valid():
            user = form.save()
            Estudiante.objects.get_or_create(
                user=user, 
                defaults={'carnet': f'E-{user.id:04d}', 'carrera': 'Informática'}
            )
            return redirect('login')
    else:
        form = RegistroForm() 
    return render(request, 'cursos/registro.html', {'form': form})
    
def inicio(request):
    cursos = Curso.objects.all()
    mensaje = request.session.pop('mensaje_exito', None)
    error = request.session.pop('mensaje_error', None)
    estudiante = None
    mis_inscripciones_ids = []
    mis_horarios_ids = []

    if request.user.is_authenticated:
        estudiante, created = Estudiante.objects.get_or_create(
            user=request.user,
            defaults={'carnet': f'E-{request.user.id:04d}', 'carrera': 'Informática'}
        )
        inscripciones_usuario = Inscripcion.objects.filter(estudiante=estudiante)
        mis_inscripciones_ids = list(inscripciones_usuario.values_list('curso_id', flat=True))
        mis_horarios_ids = list(inscripciones_usuario.filter(horario_elegido__isnull=False).values_list('horario_elegido_id', flat=True))

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
          
        accion = request.POST.get('accion')
        horario_id = request.POST.get('horario_id')
        inscripcion_id = request.POST.get('inscripcion_id')

        # 🛑 CASO 1: CANCELAR UNA INSCRIPCIÓN ÚNICA POR SU ID ESPECÍFICO
        if accion == 'cancelar' and inscripcion_id and estudiante:
            # Buscamos la inscripción exacta que pertenece a este estudiante y a este ID de registro
            inscripcion_a_borrar = get_object_or_404(Inscripcion, id=inscripcion_id, estudiante=estudiante)
            curso = inscripcion_a_borrar.curso
            horario_cancelado = inscripcion_a_borrar.horario_elegido
            
            # Eliminamos únicamente este registro en la base de datos
            inscripcion_a_borrar.delete()
            
            # Devolvemos el cupo al curso
            curso.cupos_disponibles += 1
            curso.save()
            
            dia_texto = horario_cancelado.get_dia_display() if horario_cancelado else "turno"
            hora_texto = f"{horario_cancelado.hora_inicio.strftime('%H:%M')} - {horario_cancelado.hora_fin.strftime('%H:%M')}" if horario_cancelado else ""
            
            request.session['mensaje_exito'] = f"Has cancelado exitosamente tu turno del {dia_texto} ({hora_texto}) para el curso '{curso.nombre}'."
            
            return redirect('inicio')

        # 📝 CASO 2: INSCRIBIRSE A UN CURSO POR BLOQUE ESPECÍFICO
        else:
            if horario_id and estudiante:
                horario_elegido = get_object_or_404(Horario, id=horario_id)
                curso = horario_elegido.curso
                
                if horario_elegido.id in mis_horarios_ids:
                    request.session['mensaje_error'] = f"Ya estás inscrito en este bloque horario ({horario_elegido.get_dia_display()} {horario_elegido.hora_inicio.strftime('%H:%M')} - {horario_elegido.hora_fin.strftime('%H:%M')})."
                elif curso.cupos_disponibles <= 0:
                    request.session['mensaje_error'] = "Lo sentimos, este curso ya no tiene cupos disponibles."
                else:
                    try:
                        inscripcion = Inscripcion(
                            estudiante=estudiante, 
                            curso=curso, 
                            horario_elegido=horario_elegido
                        )
                        inscripcion.full_clean()
                        inscripcion.save()
                        
                        curso.cupos_disponibles -= 1
                        curso.save()
                        
                        request.session['mensaje_exito'] = f"¡Inscripción exitosa en {curso.nombre} para el {horario_elegido.get_dia_display()} ({horario_elegido.hora_inicio.strftime('%H:%M')} - {horario_elegido.hora_fin.strftime('%H:%M')})!"
                    except ValidationError as e:
                        request.session['mensaje_error'] = e.messages[0] if hasattr(e, 'messages') else str(e)
            
            return redirect('inicio')

    return render(request, 'cursos/inicio.html', {
        'cursos': cursos,
        'mensaje': mensaje,
        'error': error,
        'mis_inscripciones_ids': mis_inscripciones_ids,
        'mis_horarios_ids': mis_horarios_ids
    })