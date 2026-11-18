from django.contrib import admin
from django.db import models
from django.forms import Textarea
from .models import Curso, Estudiante, Profesor, Horario, Inscripcion

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'profesor', 'cupos_disponibles')
    search_fields = ('nombre', 'descripcion')
    
    # 🎯 Organizamos los campos en bloques visuales para que el Admin calcule bien la altura y muestre los botones de guardar
    fieldsets = (
        ('Información Principal', {
            'fields': ('nombre', 'descripcion', 'proposito', 'profesor', 'cupos_disponibles', 'imagen')
        }),
        ('Configuración del Aula Virtual', {
            'fields': ('link_meet', 'contenido_bibliografico', 'video_youtube'),
            'description': 'Pega aquí los enlaces o el código HTML de inserción del video de YouTube.'
        }),
    )
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
    }

admin.site.register(Estudiante)
admin.site.register(Profesor)
admin.site.register(Horario)
admin.site.register(Inscripcion)