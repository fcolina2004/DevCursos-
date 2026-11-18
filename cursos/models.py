from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profesor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    proposito = models.TextField(blank=True, null=True)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    cupos_disponibles = models.PositiveIntegerField(default=20)
    imagen = models.URLField(blank=True, null=True, help_text="Pega aquí el enlace de la imagen")
    
    # 📚 CAMPOS PARA EL AULA VIRTUAL (video_youtube adaptado para recibir código HTML de inserción)
    link_meet = models.URLField(blank=True, null=True, help_text="Enlace de la sala de Google Meet")
    contenido_bibliografico = models.URLField(max_length=500, blank=True, null=True, verbose_name="Contenido Bibliográfico (Enlace directo)", help_text="Pega el enlace directo a la investigación, glosario o PDF en español")
    video_youtube = models.TextField(blank=True, null=True, verbose_name="Código HTML de inserción de YouTube", help_text="Pega aquí todo el código iframe proporcionado por YouTube")
    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"

    def __str__(self):
        return self.nombre


class Horario(models.Model):
    DIAS_SEMANA = [
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
        ('SAB', 'Sábado'),
    ]
    
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="horarios")
    dia = models.CharField(max_length=3, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.curso.nombre} - {self.get_dia_display()} ({self.hora_inicio} a {self.hora_fin})"


class Estudiante(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    carnet = models.CharField(max_length=20, unique=True, blank=True, null=True)
    carrera = models.CharField(max_length=100, default="Informática")

    def __str__(self):
        return f"{self.user.username} ({self.carnet or 'Sin carnet'})"


class Inscripcion(models.Model):
    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="inscripciones")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="inscripciones")
    horario_elegido = models.ForeignKey(Horario, on_delete=models.CASCADE, null=True, blank=True)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        super().clean()
        if not self.horario_elegido:
            return
            
        horarios_nuevo_curso = [self.horario_elegido]
        inscripciones_previas = Inscripcion.objects.filter(estudiante=self.estudiante)
        
        for inscripcion in inscripciones_previas:
            if self.pk and inscripcion.pk == self.pk:
                continue
                
            horarios_existentes = [inscripcion.horario_elegido] if inscripcion.horario_elegido else inscripcion.curso.horarios.all()
            
            for h_nuevo in horarios_nuevo_curso:
                for h_existente in horarios_existentes:
                    if h_nuevo and h_existente and h_nuevo.dia == h_existente.dia:
                        if (h_nuevo.hora_inicio < h_existente.hora_fin) and (h_nuevo.hora_fin > h_existente.hora_inicio):
                            raise ValidationError(
                                f"No es posible la inscripción. El horario seleccionado "
                                f"({h_nuevo.get_dia_display()} {h_nuevo.hora_inicio}-{h_nuevo.hora_fin}) "
                                f"se cruza con tu curso ya inscrito '{inscripcion.curso.nombre}' "
                                f"({h_existente.get_dia_display()} {h_existente.hora_inicio}-{h_existente.hora_fin})."
                            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.estudiante} -> {self.curso.nombre} ({self.horario_elegido or 'General'})"


@receiver(post_save, sender=User)
def crear_perfil_estudiante(sender, instance, created, **kwargs):
    if created:
        if not instance.is_superuser and not instance.is_staff:
            Estudiante.objects.create(
                user=instance,
                carnet=f"E-{instance.id:04d}",
                carrera="Informática"
            )