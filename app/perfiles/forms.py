from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from app.publicaciones.imagenes import ErrorImagen, preparar_imagen

from .models import Perfil


Usuario = get_user_model()


class FormularioEditarPerfil(forms.Form):
    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    telefono = forms.CharField(
        label="Teléfono",
        max_length=30,
        widget=forms.TextInput(attrs={"autocomplete": "tel"}),
    )
    foto = forms.FileField(
        label="Foto de perfil",
        required=False,
        widget=forms.FileInput(
            attrs={"accept": "image/jpeg,image/png,image/webp"}
        ),
    )
    eliminar_foto = forms.BooleanField(
        label="Quitar mi foto actual",
        required=False,
    )

    def __init__(self, usuario, perfil, *args, **kwargs):
        self.usuario = usuario
        self.perfil = perfil
        kwargs.setdefault(
            "initial",
            {
                "first_name": usuario.first_name,
                "last_name": usuario.last_name,
                "email": usuario.email,
                "telefono": usuario.telefono,
            },
        )
        super().__init__(*args, **kwargs)
        self.fields["foto"].widget.attrs["data-perfil-foto"] = ""
        self.fields["eliminar_foto"].widget.attrs["data-eliminar-foto"] = ""

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().casefold()
        if Usuario.objects.filter(email__iexact=email).exclude(
            pk=self.usuario.pk
        ).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta con ese correo electrónico."
            )
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data["telefono"].strip()
        if not telefono:
            raise forms.ValidationError("Escribe tu número de teléfono.")
        return telefono

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if not foto:
            return None
        try:
            return preparar_imagen(foto)
        except ErrorImagen as error:
            raise forms.ValidationError(str(error)) from error

    def guardar_cambios(self):
        usuario = self.usuario
        perfil = self.perfil
        email_nuevo = self.cleaned_data["email"]
        correo_cambiado = email_nuevo != usuario.email
        foto_anterior = perfil.foto.name
        almacenamiento_foto = perfil.foto.storage

        with transaction.atomic():
            usuario.first_name = self.cleaned_data["first_name"]
            usuario.last_name = self.cleaned_data["last_name"]
            usuario.email = email_nuevo
            usuario.telefono = self.cleaned_data["telefono"]
            if correo_cambiado:
                usuario.correo_verificado = False
            usuario.save(
                update_fields=[
                    "first_name",
                    "last_name",
                    "email",
                    "telefono",
                    "correo_verificado",
                ]
            )

            foto_nueva = self.cleaned_data.get("foto")
            if foto_nueva:
                perfil.foto.save(foto_nueva.name, foto_nueva, save=False)
                perfil.save(update_fields=["foto"])
            elif self.cleaned_data.get("eliminar_foto") and perfil.foto:
                perfil.foto = ""
                perfil.save(update_fields=["foto"])

        return (
            correo_cambiado,
            almacenamiento_foto,
            foto_anterior,
            perfil.foto.name,
        )
