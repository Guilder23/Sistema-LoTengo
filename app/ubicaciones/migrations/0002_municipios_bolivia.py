from django.db import migrations, models


MUNICIPIOS_POR_DEPARTAMENTO = {
    "beni": [
        "Trinidad", "San Javier", "Riberalta", "Guayaramerín", "Reyes",
        "San Borja", "Santa Rosa de Yacuma", "Rurrenabaque",
        "Santa Ana del Yacuma", "Exaltación", "San Ignacio de Moxos",
        "Loreto", "San Andrés", "San Joaquín", "San Ramón", "Puerto Siles",
        "Magdalena", "Baures", "Huacaraje",
    ],
    "chuquisaca": [
        "Sucre", "Yotala", "Poroma", "Azurduy", "Tarvita", "Zudáñez",
        "Presto", "Mojocoya", "Icla", "Padilla", "Tomina", "Sopachuy",
        "Villa Alcalá", "El Villar", "Monteagudo", "Huacareta", "Tarabuco",
        "Yamparáez", "Camargo", "San Lucas", "Incahuasi", "Villa Charcas",
        "Villa Serrano", "Camataqui (Villa Abecia)", "Culpina",
        "Las Carreras", "Villa Vaca Guzmán (Muyupampa)", "Huacaya", "Macharetí",
    ],
    "cochabamba": [
        "Cochabamba", "Aiquile", "Pasorapa", "Omereque", "Ayopaya",
        "Morochata", "Cocapata", "Tarata", "Anzaldo", "Arbieto", "Sacabamba",
        "Arani", "Vacas", "Arque", "Tacopaya", "Capinota", "Santiváñez",
        "Sicaya", "Cliza", "Toco", "Tolata", "Quillacollo", "Sipe Sipe",
        "Tiquipaya", "Vinto", "Colcapirhua", "Sacaba", "Colomi",
        "Villa Tunari", "Tapacarí", "Totora", "Pojo", "Pocona", "Chimoré",
        "Puerto Villarroel", "Entre Ríos", "Mizque", "Vila Vila", "Alalay",
        "Punata", "Villa Rivero", "San Benito", "Tacachi", "Cuchumuela",
        "Bolívar", "Tiraque", "Shinahota",
    ],
    "la_paz": [
        "Nuestra Señora de La Paz", "Palca", "Mecapaca", "Achocalla",
        "El Alto", "Achacachi", "Ancoraimes", "Chua Cocani", "Huarina",
        "Santiago de Huata", "Huatajata", "Coro Coro", "Caquiaviri",
        "Calacoto", "Comanche", "Charaña", "Waldo Ballivián",
        "Nazacara de Pacajes", "Santiago de Callapa", "Puerto Acosta",
        "Mocomoco", "Puerto Carabuco", "Humanata", "Escoma", "Chuma",
        "Ayata", "Aucapata", "Sorata", "Guanay", "Tacacoma", "Quiabaya",
        "Combaya", "Tipuani", "Mapiri", "Teoponte", "Apolo", "Pelechuco",
        "Viacha", "Guaqui", "Tiahuanacu", "Desaguadero",
        "San Andrés de Machaca", "Jesús de Machaca", "Taraco", "Luribay",
        "Sapahaqui", "Yaco", "Malla", "Cairoma", "Inquisivi", "Quime",
        "Cajuata", "Colquiri", "Ichoca", "Villa Libertad Licoma", "Chulumani",
        "Irupana", "Yanacachi", "Palos Blancos", "La Asunta", "Pucarani",
        "Laja", "Batallas", "Puerto Pérez", "Copacabana", "San Pedro de Tiquina",
        "Tito Yupanqui", "San Pedro de Curahuara", "Papel Pampa",
        "Chacarilla", "Santiago de Machaca", "Catacora", "Caranavi",
        "Alto Beni", "Coroico", "Coripata", "Ixiamas", "San Buenaventura",
        "General Juan José Pérez (Charazani)", "Curva",
    ],
    "oruro": [
        "Oruro", "Caracollo", "El Choro", "Paria (Soracachi)", "Challapata",
        "Santuario de Quillacas", "Corque", "Choque Cota",
        "Curahuara de Carangas", "Turco", "Huachacalla", "Escara",
        "Cruz de Machacamarca", "Yunguyo del Litoral", "Esmeralda", "Poopó",
        "Pazña", "Antequera", "Huanuni", "Machacamarca",
        "Salinas de Garcí Mendoza", "Pampa Aullagas", "Sabaya", "Coipasa",
        "Chipaya", "Toledo", "Eucaliptus", "Santiago de Andamarca",
        "Belén de Andamarca", "Totora", "Santiago de Huari", "La Rivera",
        "Todos Santos", "Carangas", "Huayllamarca",
    ],
    "pando": [
        "Cobija", "Porvenir", "Bolpebra", "Bella Flor", "Puerto Rico",
        "San Pedro", "Filadelfia", "Puerto Gonzalo Moreno", "San Lorenzo",
        "Sena", "Santa Rosa del Abuná", "Ingavi (Humaitá)",
        "Nueva Esperanza", "Villa Nueva (Loma Alta)", "Santos Mercado",
    ],
    "potosi": [
        "Potosí", "Tinguipaya", "Yocalla", "Urmiri", "Uncía", "Chayanta",
        "Llallagua", "Chuquihuta", "Betanzos", "Chaquí", "Tacobamba",
        "Colquechaca", "Ravelo", "Pocoata", "Ocurí", "San Pedro de Macha",
        "San Pedro de Buena Vista", "Toro Toro", "Cotagaita", "Vitichi",
        "Sacaca", "Caripuyo", "Tupiza", "Atocha", 'Colcha "K"',
        "San Pedro de Quemes", "San Pablo de Lípez", "Mojinete",
        "San Antonio de Esmoruco", "Puna", 'Caiza "D"', "Ckochas", "Uyuni",
        "Tomave", "Porco", "Arampampa", "Acasio", "Llica", "Tahua",
        "Villazón", "San Agustín",
    ],
    "santa_cruz": [
        "Santa Cruz de la Sierra", "Cotoca", "Porongo", "La Guardia",
        "El Torno", "Warnes", "Okinawa Uno", "San Ignacio de Velasco",
        "San Miguel de Velasco", "San Rafael de Velasco", "Buena Vista",
        "San Carlos", "Yapacaní", "San Juan de Yapacaní",
        "San José de Chiquitos", "Pailón", "Roboré", "Portachuelo",
        "Santa Rosa del Sara", "Colpa Bélgica", "Lagunillas", "Charagua",
        "Cabezas", "Cuevo", "Gutiérrez", "Camiri", "Boyuibe", "Vallegrande",
        "Trigal", "Moro Moro", "Postrervalle", "Pucará", "Samaipata",
        "Pampa Grande", "Mairana", "Quirusillas", "Montero",
        "General Saavedra", "Mineros", "Fernández Alonso", "San Pedro",
        "Concepción", "San Javier", "San Ramón", "San Julián",
        "San Antonio de Lomerío", "Cuatro Cañadas", "San Matías", "Comarapa",
        "Saipina", "Puerto Suárez", "Puerto Quijarro",
        "El Carmen Rivero Tórrez", "Ascensión de Guarayos", "Urubichá",
        "El Puente",
    ],
    "tarija": [
        "Tarija", "Padcaya", "Bermejo", "Yacuiba", "Caraparí",
        "Villamontes", "Uriondo", "Yunchará", "San Lorenzo", "El Puente",
        "Entre Ríos",
    ],
}


def cargar_municipios(apps, schema_editor):
    Municipio = apps.get_model("ubicaciones", "Municipio")
    for departamento, municipios in MUNICIPIOS_POR_DEPARTAMENTO.items():
        for municipio in municipios:
            Municipio.objects.update_or_create(
                departamento=departamento,
                nombre=municipio,
            )


def eliminar_municipios(apps, schema_editor):
    Municipio = apps.get_model("ubicaciones", "Municipio")
    Municipio.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ubicaciones", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Municipio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("departamento", models.CharField(choices=[("beni", "Beni"), ("chuquisaca", "Chuquisaca"), ("cochabamba", "Cochabamba"), ("la_paz", "La Paz"), ("oruro", "Oruro"), ("pando", "Pando"), ("potosi", "Potosí"), ("santa_cruz", "Santa Cruz"), ("tarija", "Tarija")], max_length=20)),
                ("nombre", models.CharField(max_length=100)),
            ],
            options={
                "verbose_name": "municipio",
                "verbose_name_plural": "municipios",
                "ordering": ["departamento", "nombre"],
            },
        ),
        migrations.AddConstraint(
            model_name="municipio",
            constraint=models.UniqueConstraint(fields=("departamento", "nombre"), name="ubicaciones_municipio_departamento_nombre_unicos"),
        ),
        migrations.RunPython(cargar_municipios, eliminar_municipios),
    ]
