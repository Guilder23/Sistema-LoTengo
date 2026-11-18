# **EncontrApp: planificación completa de la página web**

Vamos a desarrollar **EncontrApp primero como una página web adaptable a celulares y computadoras**, utilizando Django. Desde el inicio tendrá tres tipos de usuario:

1. **Administrador:** controla la plataforma, usuarios, publicaciones, denuncias, pagos y seguridad.
2. **Persona que encuentra:** registra objetos que encontró y ayuda a devolverlos.
3. **Persona que busca:** registra objetos que perdió y busca coincidencias.

Una misma persona podrá cumplir los dos últimos roles. Por ejemplo, alguien puede perder su celular hoy y encontrar una mochila mañana. Por eso, recomiendo que no sean cuentas separadas: cada usuario tendrá un solo registro y podrá publicar tanto objetos perdidos como encontrados.

## **1. Cómo funcionará EncontrApp**

## **Flujo principal de recuperación**

1. **Publicación:** alguien registra un objeto perdido o encontrado.
2. **Búsqueda:** el sistema muestra publicaciones relacionadas por categoría, características, fecha y ubicación.
3. **Coincidencia:** una persona identifica una posible coincidencia y solicita contacto.
4. **Chat privado:** ambas personas conversan dentro de EncontrApp.
5. **Verificación:** quien reclama demuestra que el objeto le pertenece.
6. **Entrega:** acuerdan un lugar público y realizan la devolución.
7. **Confirmación:** ambas personas confirman la recuperación.
8. **Pago:** si corresponde cobrar el servicio, se muestra el QR estático y se verifica el pago.
9. **Cierre:** el objeto pasa al estado recuperado y queda registrado en el historial.

**Una decisión importante:** el chat será gratuito. No conviene cobrar por enviar mensajes ni impedir que las personas se comuniquen. El cobro se aplicará al servicio de recuperación, si finalmente se adopta ese modelo, y deberá estar explicado antes de que el usuario lo acepte.

## **2. Módulos y funciones de la plataforma**

Esta sería la estructura funcional que recomiendo. La idea es construirla desde el principio con los controles importantes, aunque algunas funciones avanzadas puedan activarse en una segunda etapa.

### **Módulo 1. Página pública**

No es necesario iniciar sesión para conocer la plataforma o consultar publicaciones públicas.

- Página de inicio con explicación de cómo funciona EncontrApp.
- Buscador de objetos perdidos y encontrados.
- Listado de publicaciones recientes.
- Filtros por categoría.
- Filtros por departamento, municipio y zona.
- Sección de instrucciones para recuperar un objeto.
- Preguntas frecuentes.
- Página de contacto y soporte.
- Página de seguridad y recomendaciones para las entregas.
- Enlaces a términos y condiciones, política de privacidad y política de cookies.
- Aviso visible de que EncontrApp conecta personas, pero no garantiza por sí misma la propiedad ni la devolución de un objeto.

**Importante:** se puede mostrar información general de las publicaciones sin revelar información privada. Para contactar, enviar mensajes o publicar, el usuario deberá registrarse.

### **Módulo 2. Registro, inicio de sesión y cuentas**

Funciones:

- Registro con nombres y apellidos.
- Correo electrónico.
- Número de celular.
- Contraseña.
- Confirmación de contraseña.
- Verificación del correo electrónico.
- Verificación del número de celular mediante código, si se habilita un proveedor de SMS.
- Inicio y cierre de sesión.
- Recuperación de contraseña.
- Cambio de contraseña.
- Edición del perfil.
- Foto de perfil opcional.
- Aceptación de términos y condiciones.
- Aceptación de política de privacidad.
- Registro de fecha y versión de los documentos aceptados.
- Desactivación de cuenta.
- Solicitud de eliminación de cuenta y datos, según las obligaciones de conservación aplicables.

**Cómo funcionará:** al registrarse, una persona tendrá una cuenta. Desde esa misma cuenta podrá publicar objetos perdidos y encontrados. El administrador tendrá permisos diferentes y no se registrará mediante el formulario público.

### **Módulo 3. Perfil del usuario**

Cada usuario tendrá:

- Nombre visible.
- Foto de perfil opcional.
- Municipio y departamento.
- Fecha de registro.
- Cantidad de publicaciones.
- Objetos devueltos, si se han confirmado.
- Estado de la cuenta: activa, suspendida o bloqueada.
- Historial de actividad propio.
- Configuración de notificaciones.
- Opción para cambiar contraseña.
- Opción para cerrar sesiones en otros dispositivos.
- Opción para solicitar eliminación de cuenta.

No mostrar públicamente:

- Correo electrónico.
- Número de teléfono.
- Número de carnet.
- Dirección particular.
- Ubicación exacta.
- Datos personales innecesarios.

### **Módulo 4. Publicaciones de objetos perdidos**

Este módulo lo utilizará quien perdió algo.

Funciones:

1. Crear una publicación de objeto perdido.
2. Seleccionar categoría.
3. Escribir título.
4. Describir el objeto.
5. Adjuntar fotografías, si tiene.
6. Registrar fecha aproximada de pérdida.
7. Seleccionar departamento.
8. Seleccionar municipio.
9. Indicar zona o lugar aproximado.
10. Seleccionar si conoce el lugar exacto o aproximado.
11. Agregar características particulares.
12. Editar publicación.
13. Desactivar publicación.
14. Eliminar publicación, respetando los registros que deban conservarse.
15. Marcar objeto como recuperado.
16. Consultar personas interesadas o posibles coincidencias.
17. Consultar el historial de contactos.
18. Reportar una publicación sospechosa.

Categorías iniciales:

- Documentos personales.
- Carnets y tarjetas.
- Celulares y dispositivos electrónicos.
- Mochilas y bolsos.
- Llaves.
- Ropa y accesorios.
- Dinero y billeteras.
- Mascotas.
- Otros objetos.

**Seguridad:** si alguien pierde su carnet, no debe publicar una fotografía donde se lean todos sus datos. La plataforma debe advertirlo y, si es posible, detectar o bloquear imágenes con información sensible.

### **Módulo 5. Publicaciones de objetos encontrados**

Este módulo lo utilizará quien encontró algo.

Funciones:

1. Crear publicación de objeto encontrado.
2. Seleccionar categoría.
3. Escribir título.
4. Agregar descripción.
5. Adjuntar fotografías.
6. Registrar fecha en que encontró el objeto.
7. Indicar ubicación aproximada.
8. Seleccionar departamento y municipio.
9. Indicar características visibles.
10. Editar publicación.
11. Desactivar publicación.
12. Marcar objeto como entregado.
13. Consultar posibles propietarios.
14. Consultar solicitudes de recuperación.
15. Consultar conversaciones relacionadas.
16. Reportar a un usuario sospechoso.

**Una protección importante:** la persona que publica un objeto encontrado debe poder ocultar características que permitan identificarlo con precisión.

Por ejemplo:

- Información pública: mochila negra encontrada cerca de una universidad.
- Información privada: tiene un llavero rojo dentro del bolsillo delantero.

La persona que reclama deberá describir esa característica privada para ayudar a demostrar que es suya.

### **Módulo 6. Buscador y filtros**

El buscador será una de las funciones más importantes de EncontrApp.

Funciones:

- Buscar por nombre del objeto.
- Buscar por descripción.
- Buscar por categoría.
- Buscar por fecha.
- Buscar por municipio.
- Buscar por departamento.
- Buscar por zona.
- Filtrar objetos perdidos.
- Filtrar objetos encontrados.
- Ordenar por fecha de publicación.
- Mostrar publicaciones recientes.
- Mostrar publicaciones cercanas según la ubicación aproximada.
- Guardar búsquedas.
- Marcar publicaciones como favoritas.

**Ejemplo:** alguien perdió un celular Samsung negro en Cochabamba. Podrá buscar celulares encontrados en Cochabamba, filtrar por fecha y revisar publicaciones similares.

### **Módulo 7. Coincidencias entre objetos perdidos y encontrados**

Este módulo relacionará automáticamente las publicaciones.

El sistema comparará:

- Categoría.
- Nombre del objeto.
- Marca.
- Color.
- Características.
- Fecha de pérdida y fecha de hallazgo.
- Departamento.
- Municipio.
- Zona aproximada.
- Descripción.

Ejemplo:

**Posible coincidencia**

Alta similitud

[Front view of the black smartphone isolated on white background.](https://images.openai.com/static-rsc-4/xqTY2dmBNCFslwGN7OISOkdml1UrhThsLdnCJhaPzsPYYn2UaRE_ydjuXMAn2WLuphWAA9V6U9n_DIdNNw-TF5p7VdvlAg8cLNA-6lILlrxHdZ5JhEB6zeglJ6Ter7xkpFIl7u4ijDalkUni9XlSHXJoQ-h5IRUwyaPxtljOz-dlI97pMYTzPO6iZFn7lHqr?purpose=inline)

**Objeto perdido**

Celular negro, marca Samsung. Perdido cerca de la UMSS.

Fecha: 15 de noviembre

[YEN- smartphone HD Téléphone portable HD 6,5 pouces 4G LTE 5G WIFI double bande 4 Go 64 Go MT6735 Quad Core CPU avant 500 W - Cdiscount Téléphonie](https://images.openai.com/static-rsc-4/Dv-Oh7sWYBJ3p78tfoMyt0qWUOqJd-3IyRADBuGgHGYZymJjhwtcbUuk1Gd3Tzb1mqK1jv8Ki5BKjZa_wmU85OHG5xU9xyjAXYuV3e-MYM8xtGa_CqUKHrL-sjjSf2fGfJQwGAOgfO2ZKaz1POncZ6HKEiK714ngW_u-f9gG99Q?purpose=inline)

**Objeto encontrado**

Celular negro encontrado cerca de la universidad.

Fecha: 15 de noviembre

La coincidencia es una sugerencia, no una confirmación de propiedad.

Funciones del módulo:

- Generar coincidencias automáticas.
- Calcular una puntuación de similitud.
- Mostrar coincidencias al usuario.
- Enviar notificación de posible coincidencia.
- Permitir que el usuario indique si le interesa.
- Evitar duplicar avisos sobre la misma pareja de publicaciones.
- Registrar si la coincidencia fue aceptada, descartada o resuelta.

No hace falta inteligencia artificial avanzada para comenzar. Podemos desarrollar un algoritmo de comparación con Django y PostgreSQL. Más adelante se puede incorporar reconocimiento de imágenes.

### **Módulo 8. Chat privado**

Sí, el chat estará disponible desde el principio.

Funciones:

- Conversaciones entre dos usuarios.
- Chat asociado a una publicación.
- Mensajes de texto.
- Envío de fotografías.
- Fecha y hora de cada mensaje.
- Indicador de mensajes leídos.
- Notificaciones de mensajes nuevos.
- Historial de conversaciones.
- Archivar conversaciones.
- Bloquear a un usuario.
- Reportar una conversación.
- Cerrar una conversación.
- Consultar la publicación relacionada desde el chat.

**Reglas de privacidad:**

- No mostrar automáticamente teléfonos ni correos.
- No permitir que cualquier usuario contacte masivamente a otros.
- Limitar el envío repetitivo de mensajes.
- No permitir archivos ejecutables.
- Validar imágenes y tamaño de archivos.
- Advertir que no se debe compartir información bancaria, claves ni documentos personales.
- No prometer que será imposible intercambiar teléfonos: una persona podría escribir su número en un mensaje o en una imagen.

Para hacerlo en tiempo real, recomiendo **Django Channels y WebSockets**. También se puede comenzar con un chat que actualice los mensajes periódicamente y luego mejorarlo.

### **Módulo 9. Solicitudes de recuperación**

Este módulo controlará todo el proceso de devolución.

Funciones:

- Enviar solicitud para reclamar un objeto encontrado.
- Seleccionar la publicación relacionada.
- Describir características privadas del objeto.
- Adjuntar pruebas de propiedad, si corresponde.
- Aceptar o rechazar una solicitud.
- Enviar una solicitud adicional de verificación.
- Iniciar conversación.
- Registrar acuerdo de entrega.
- Registrar fecha y lugar aproximado de entrega.
- Confirmar que el objeto fue entregado.
- Confirmar que el objeto fue recibido.
- Abrir una disputa si existe desacuerdo.
- Consultar el estado de la recuperación.

Estados recomendados:

| Estado            | Significado                                                  |
| ----------------- | ------------------------------------------------------------ |
| Pendiente         | Se envió la solicitud                                        |
| En revisión       | Se están verificando los datos                               |
| Aceptada          | La persona que encontró acepta conversar sobre la devolución |
| Entrega acordada  | Ambas partes acordaron coordinar                             |
| Entrega pendiente | Todavía no se confirma la devolución                         |
| Recuperado        | Ambas partes confirmaron                                     |
| En disputa        | Existe desacuerdo                                            |
| Cancelado         | La solicitud fue cancelada                                   |

No debe existir una confirmación automática de recuperación por el simple hecho de que se inició un chat.

### **Módulo 10. Pagos con QR estático**

Para empezar, utilizaremos un QR bancario estático. No necesitaremos una integración con una pasarela de pagos.

Mi recomendación es que el QR se utilice únicamente cuando exista una recuperación confirmada y el usuario haya sido informado previamente del costo.

Funciones:

1. Configurar el importe del servicio desde el administrador.
2. Mostrar el precio en bolivianos.
3. Mostrar el QR estático.
4. Mostrar el nombre del titular de la cuenta.
5. Explicar cómo realizar el pago.
6. Permitir adjuntar una fotografía del comprobante.
7. Registrar el pago asociado a una recuperación.
8. Permitir que el administrador revise el comprobante.
9. Aprobar el pago.
10. Rechazar el pago si no se puede verificar.
11. Registrar fecha de revisión.
12. Registrar quién verificó el pago.
13. Generar un comprobante interno de la operación.
14. Consultar el historial de pagos.

Estados del pago:

- Pendiente.
- Comprobante enviado.
- En verificación.
- Pagado.
- Rechazado.
- Anulado.
- En revisión por reclamo.

**Ejemplo de pantalla de pago**

Pago por servicio de recuperación

# **Bs 5,00**

[BANCOMAT Pay - isybank](https://images.openai.com/static-rsc-4/OS3_ye9mf4RufIL_6zMdwlHRCMQKzRxmqIUp5McxXSUjHThqX547A7xr3Jp5daocOZQNtl_VPwB4eYlWhkt-DwizVAOpK-ryIXpavlEa4kdkOG5TNd4yM2TsTffova5AidQgIEjdnhNegta5d-fUXyYPH2MH4D18F9XWZmeZeGk?purpose=inline)

Imagen ilustrativa. El QR real será el proporcionado por el banco.

- Escanea el QR desde tu aplicación bancaria.
- Verifica el nombre del destinatario y el importe.
- Realiza el pago.
- Adjunta tu comprobante.
- Espera la verificación.

  Pago pendiente de verificación

**Cuidados importantes con el QR estático:**

- No confiar únicamente en la imagen del comprobante.
- El administrador debe comprobar el abono en la cuenta bancaria.
- No marcar automáticamente un pago como confirmado.
- No almacenar claves bancarias.
- No publicar el QR en lugares donde pueda ser reemplazado por uno falso.
- Mostrar claramente a nombre de quién se paga.
- Registrar quién aprobó el pago.
- Mantener un historial de cambios.

Un QR estático no permite que Django confirme por sí solo que el dinero llegó. La verificación será manual hasta integrar una solución bancaria con API.

También debemos decidir si el cobro será una tarifa fija o si habrá excepciones. No recomiendo cobrar a quien encontró y devolvió el objeto.

### **Módulo 11. Notificaciones**

- Nueva coincidencia.
- Nuevo mensaje.
- Nueva solicitud de recuperación.
- Solicitud aceptada.
- Solicitud rechazada.
- Entrega acordada.
- Confirmación de entrega.
- Pago pendiente.
- Pago aprobado.
- Pago rechazado.
- Respuesta a una denuncia.
- Cambios importantes en la cuenta.

Las notificaciones podrán aparecer dentro de la web. Después podemos incorporar notificaciones push mediante PWA, sin que sea obligatorio instalar una aplicación.

### **Módulo 12. Favoritos e historial**

- Guardar publicaciones favoritas.
- Eliminar de favoritos.
- Ver publicaciones consultadas.
- Ver objetos perdidos publicados.
- Ver objetos encontrados publicados.
- Ver solicitudes realizadas.
- Ver recuperaciones completadas.
- Ver conversaciones.
- Ver pagos.
- Consultar estados anteriores de las publicaciones.

### **Módulo 13. Denuncias, bloqueos y moderación**

Este módulo es indispensable para generar confianza.

Funciones:

- Reportar publicación falsa.
- Reportar objeto sospechoso.
- Reportar intento de estafa.
- Reportar acoso.
- Reportar mensajes inapropiados.
- Reportar intento de suplantación.
- Bloquear usuario.
- Silenciar conversación.
- Adjuntar pruebas.
- Registrar motivo de denuncia.
- Consultar el estado de la denuncia.
- Permitir que el administrador responda.
- Suspender temporalmente cuentas.
- Bloquear definitivamente cuentas en casos justificados.
- Ocultar publicaciones mientras se revisan.
- Registrar las decisiones de moderación.

### **Módulo 14. Panel de administración**

El administrador será el encargado de gestionar la plataforma.

## **Panel de administrador**

Usuarios registrados

# **1.250**

Publicaciones activas

# **340**

Recuperaciones

# **86**

Denuncias pendientes

# **4**

Ejemplo ilustrativo del diseño, no son datos reales.

Funciones del administrador:

**Usuarios**

- Listar usuarios.
- Buscar por nombre, correo o celular.
- Ver perfil.
- Ver publicaciones.
- Suspender cuenta.
- Reactivar cuenta.
- Bloquear cuenta.
- Consultar historial de denuncias.

**Publicaciones**

- Listar publicaciones.
- Buscar y filtrar.
- Revisar fotografías.
- Ocultar publicaciones.
- Eliminar publicaciones que incumplan las reglas.
- Consultar cambios realizados.
- Ver publicaciones denunciadas.

**Recuperaciones**

- Consultar solicitudes.
- Revisar disputas.
- Consultar entregas pendientes.
- Ver confirmaciones de ambas partes.
- Intervenir en casos reportados.
- Registrar resolución y motivo.

**Pagos**

- Configurar tarifa.
- Consultar comprobantes.
- Verificar depósitos.
- Aprobar o rechazar pagos.
- Consultar ingresos.
- Descargar reportes.
- Consultar quién verificó cada pago.

**Denuncias**

- Consultar denuncias pendientes.
- Revisar pruebas.
- Responder al usuario.
- Suspender cuentas.
- Registrar resolución.
- Consultar historial.

**Configuración**

- Nombre y logotipo.
- Correo de contacto.
- Número de soporte.
- QR bancario.
- Titular de la cuenta.
- Tarifas.
- Categorías.
- Departamentos y municipios.
- Límites de imágenes y archivos.
- Mensajes automáticos.
- Términos y condiciones publicados.
- Política de privacidad publicada.

**Auditoría**

- Registro de inicio de sesión del administrador.
- Cambios de tarifas.
- Aprobaciones de pagos.
- Suspensiones.
- Eliminaciones.
- Modificaciones de publicaciones.
- Cambios de configuración.

El administrador no debería tener acceso libre a las contraseñas ni a los mensajes privados de todos los usuarios. Para atender una denuncia, debe existir un procedimiento limitado y registrado para consultar la información necesaria.

## **3. Seguridad: lo que debe tener desde el principio**

EncontrApp manejará datos personales, fotografías, ubicaciones, conversaciones y comprobantes de pago. Por eso, la seguridad no puede dejarse para después.

### **3.1. Seguridad de las cuentas**

- Contraseñas almacenadas con el sistema seguro de Django, nunca en texto plano.
- Validación de contraseñas débiles.
- Recuperación de contraseña mediante enlace temporal.
- Verificación de correo.
- Protección contra intentos repetidos de inicio de sesión.
- Cierre de sesión.
- Caducidad de sesiones.
- Protección contra secuestro de sesión.
- Autenticación de dos factores para administradores.
- Permisos diferenciados para cada tipo de usuario.
- Registro de accesos administrativos.

### **3.2. Protección de datos personales**

- No mostrar teléfonos públicamente.
- No mostrar correos públicamente.
- No mostrar domicilios particulares.
- No mostrar números completos de documentos.
- No publicar ubicación exacta de objetos sensibles.
- No solicitar datos personales que no sean necesarios.
- Permitir corregir datos del perfil.
- Permitir solicitar la eliminación de la cuenta.
- Informar qué datos se recopilan y para qué se utilizan.
- Establecer cuánto tiempo se conservan los datos.
- Limitar el acceso interno a los datos.
- No vender información personal.
- No utilizar fotografías de documentos para publicidad ni otros fines.

### **3.3. Protección de fotografías y archivos**

Los usuarios podrán subir fotografías, pero debemos establecer controles:

- Permitir solamente formatos de imagen autorizados.
- Validar el contenido real del archivo, no solamente su extensión.
- Limitar el tamaño de las fotografías.
- Cambiar el nombre de los archivos al almacenarlos.
- Evitar que se ejecuten archivos subidos.
- Eliminar metadatos EXIF, especialmente coordenadas GPS.
- Almacenar archivos fuera de las carpetas ejecutables del servidor.
- Aplicar controles para evitar que se publiquen fotografías con información sensible.
- Permitir que el administrador retire fotografías denunciadas.

### **3.4. Protección del chat**

- Solo los participantes pueden acceder a una conversación.
- Nadie puede consultar conversaciones ajenas modificando una dirección URL.
- Validar cada mensaje en el servidor.
- Limitar mensajes repetitivos.
- Bloquear usuarios.
- Reportar mensajes.
- Proteger las imágenes compartidas.
- Evitar que se envíen archivos peligrosos.
- Registrar los eventos relevantes para investigar denuncias.
- Establecer una política de conservación de conversaciones.

No recomiendo prometer que el chat es completamente privado o cifrado de extremo a extremo si no implementamos y verificamos esa tecnología.

### **3.5. Protección contra ataques**

| Riesgo                        | Protección                                  |
| ----------------------------- | ------------------------------------------- |
| SQL Injection                 | ORM de Django y consultas seguras           |
| XSS                           | Escape de contenido y validación            |
| CSRF                          | Protección CSRF de Django                   |
| Fuerza bruta                  | Límites de intentos y bloqueos temporales   |
| Robo de sesión                | Cookies seguras y HTTPS                     |
| Acceso indebido               | Permisos en el servidor                     |
| Subida de archivos maliciosos | Validación y almacenamiento seguro          |
| Spam                          | Límites por usuario y controles automáticos |
| Bots                          | CAPTCHA o controles equivalentes            |
| Pérdida de información        | Copias de seguridad                         |

También recomiendo:

- HTTPS obligatorio.
- Firewall.
- Actualización periódica de Django y dependencias.
- Variables de entorno para contraseñas y claves.
- Base de datos PostgreSQL sin acceso público.
- Copias de seguridad cifradas.
- Pruebas de restauración de copias.
- Monitoreo de errores y disponibilidad.
- Separar los entornos de desarrollo y producción.

**Regla fundamental:** no basta con ocultar un botón en el frontend. Django debe comprobar los permisos en cada operación.

## **4. Seguridad especial para la devolución de objetos**

Este apartado es particularmente importante porque EncontrApp puede ser utilizado para intentar apropiarse de objetos ajenos.

### **Verificación de propiedad**

Antes de entregar un objeto, el propietario deberá demostrar que realmente le pertenece.

Ejemplos:

| Objeto    | Preguntas de verificación                          |
| --------- | -------------------------------------------------- |
| Celular   | ¿Qué marca, modelo, color o característica tiene?  |
| Mochila   | ¿Qué contiene? ¿Tiene alguna marca particular?     |
| Llaves    | ¿Cuántas llaves tiene? ¿Tiene un llavero especial? |
| Billetera | ¿Qué características tiene por dentro?             |
| Documento | ¿Puedes verificar los datos sin publicarlos?       |
| Mascota   | ¿Qué características particulares tiene?           |

No deben mostrarse todas las respuestas en la publicación. La plataforma debe permitir que quien encontró el objeto reserve información para verificar al propietario.

### **Entrega segura**

- Recomendar lugares públicos.
- No recomendar encuentros en domicilios privados.
- Advertir que no deben entregar dinero para recibir un objeto sin verificar primero el caso.
- No compartir contraseñas ni códigos de desbloqueo.
- No publicar ubicaciones exactas de objetos valiosos.
- Permitir denunciar solicitudes sospechosas.
- Registrar la confirmación de ambas partes.
- Permitir abrir una disputa.

### **Objetos que necesitan tratamiento especial**

No todos los objetos encontrados deben gestionarse de la misma manera.

Por ejemplo:

- Armas y municiones: no gestionar su devolución mediante encuentros particulares; orientar a las autoridades.
- Sustancias ilegales: no permitir publicaciones que promuevan su intercambio.
- Tarjetas bancarias: advertir que deben comunicarse con el banco emisor.
- Documentos oficiales: recomendar los canales correspondientes de la institución emisora cuando proceda.
- Objetos que puedan ser evidencia de un delito: no manipular ni organizar su entrega sin orientación de la autoridad competente.
- Mascotas: incorporar recomendaciones especiales para evitar suplantaciones y entregas inseguras.

También recomiendo que el sitio no permita publicar contenido que facilite actividades ilegales.

## **5. Condiciones legales para operar en Bolivia**

Aquí debemos distinguir dos cosas: **que la página sea técnicamente segura y que la actividad que realiza esté correctamente organizada desde el punto de vista legal**. Una no reemplaza a la otra.

He revisado normativa boliviana relacionada con datos personales, comercio electrónico y derechos de los consumidores.

### **5.1. Protección de datos personales**

El Decreto Supremo 1793, en su artículo 56, contempla el consentimiento para el tratamiento de datos personales y la información previa sobre las finalidades, los destinatarios y la identidad del responsable, además de derechos relacionados con el acceso, rectificación, actualización, cancelación y oposición.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.wipo.int\&sz=32)

WIPO



Por eso, EncontrApp debe tener:

- Política de privacidad.
- Consentimiento informado.
- Finalidad específica para cada dato recopilado.
- Información sobre el responsable del tratamiento.
- Información sobre los proveedores que puedan procesar datos.
- Procedimiento para solicitudes de acceso y corrección.
- Procedimiento para solicitudes de cancelación y revocación, cuando corresponda.
- Medidas de protección de los datos.
- Política de conservación y eliminación.

No debemos utilizar los datos para finalidades distintas de las informadas sin la base legal correspondiente.

### **5.2. Comercio electrónico y contratación digital**

La Ley 164 contempla la oferta electrónica de bienes y servicios y la validez de determinadas transacciones realizadas mediante documentos digitales. Su artículo 85 hace referencia a un ambiente técnicamente confiable.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.justicia.gob.bo\&sz=32)

Justicia+1



Por eso debemos disponer de:

- Términos y condiciones.
- Información clara sobre el servicio.
- Precio y forma de pago, cuando exista un cobro.
- Identificación del responsable.
- Mecanismo de aceptación de las condiciones.
- Registro de la aceptación.
- Mecanismo para presentar reclamos.
- Información sobre las limitaciones del servicio.

### **5.3. Derechos del consumidor**

La Ley 453 establece derechos de información, trato equitativo y reclamación. También contempla obligaciones de los proveedores sobre seguridad y confidencialidad de la información.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.autoridadempresas.gob.bo\&sz=32)

Autoridad de Empresas+2



Si EncontrApp cobra por un servicio de recuperación, debe informar claramente:

- Qué servicio está cobrando.
- Cuánto cuesta.
- Quién recibe el pago.
- Cuándo se considera que el servicio fue prestado.
- Cómo se verifica el pago.
- Qué sucede si existe una disputa.
- Qué sucede si la recuperación no se concreta.
- Cómo puede presentar un reclamo.

No se debe cobrar una tarifa que el usuario desconoce o que no aceptó.

### **5.4. Formalización de la actividad**

Si vas a operar EncontrApp de manera habitual y obtener ingresos, debes consultar cómo formalizar esa actividad.

En Bolivia, el SEPREC contempla la inscripción de comerciantes individuales o empresas unipersonales. El SIN también establece requisitos de inscripción tributaria según la actividad económica.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.gob.bo\&sz=32)

Plataforma gob.bo+2



Debes consultar:

1. Si conviene operar como empresa unipersonal o sociedad.
2. Qué actividad económica corresponde registrar.
3. Qué obligaciones tributarias corresponden.
4. Si necesitas matrícula de comercio.
5. Si necesitas licencia municipal de funcionamiento según el lugar y modalidad de operación.
6. Cómo documentar los ingresos y emitir los documentos fiscales que correspondan.

Enlaces oficiales:

- [Inscripción de comerciante individual o empresa unipersonal – SEPREC](https://www.gob.bo/tramites/tramite-01-inscripcion-de-comerciante-individual-o-empresa-unipersonal?utm_source=chatgpt.com)
- [Requisitos para obtener el NIT – SIN](https://siatanexo.impuestos.gob.bo/index.php/requisitos-para-la-inscripcion/requisitos-para-obtener-el-nit-para-personas?utm_source=chatgpt.com)
- [Ley 453 – Derechos de usuarios y consumidores](https://www.autoridadempresas.gob.bo/wp-content/uploads/2024/03/Ley-N%C2%B0-453-LGDUUCC.pdf?utm_source=chatgpt.com)
- [Ley 164 – Telecomunicaciones y tecnologías de información](https://www.justicia.gob.bo/cms/files/LEY%20N%C2%BA%20164%20Gaceta%20Oficial_gs7rr7i4.pdf?utm_source=chatgpt.com)

**Importante:** esto es una guía de cumplimiento para diseñar el sistema, no una certificación de que EncontrApp ya cumple todas las obligaciones legales. Antes de cobrar y lanzar públicamente, recomiendo que un abogado y un contador bolivianos revisen la actividad concreta, los contratos y el tratamiento tributario.

## **6. Documentos legales que tendrá la página**

Recomiendo crear una sección llamada **Información legal** en el pie de página.

| Documento                          | Para qué sirve                    |
| ---------------------------------- | --------------------------------- |
| Términos y condiciones             | Establece las reglas de uso       |
| Política de privacidad             | Explica el tratamiento de datos   |
| Política de cookies                | Explica las cookies utilizadas    |
| Política de publicaciones          | Define qué se puede publicar      |
| Política de seguridad              | Explica cómo prevenir riesgos     |
| Política de pagos                  | Explica tarifas y verificación    |
| Política de reclamaciones          | Establece cómo presentar reclamos |
| Política de eliminación de cuentas | Explica cómo solicitar la baja    |

### **Puntos que deben incluir los términos y condiciones**

1. Identificación del responsable de EncontrApp.
2. Descripción del servicio.
3. Requisitos para registrarse.
4. Responsabilidades de los usuarios.
5. Reglas para publicar objetos.
6. Prohibición de publicaciones ilegales o fraudulentas.
7. Funcionamiento del chat.
8. Procedimiento para solicitar una recuperación.
9. Reglas de verificación de propiedad.
10. Condiciones de entrega.
11. Tarifas y pagos, si se implementan.
12. Procedimiento de reclamos y disputas.
13. Suspensión de cuentas.
14. Eliminación de publicaciones.
15. Limitaciones de responsabilidad.
16. Protección de datos.
17. Modificaciones de las condiciones.
18. Canales de contacto.

Hay una distinción que debe quedar muy clara: EncontrApp es una plataforma de intermediación y comunicación. No debe afirmar que garantiza que un objeto sea auténtico, que quien lo publica sea su propietario o que la entrega siempre se realice correctamente. Pero tampoco puede utilizar esa condición para evadir responsabilidades que legalmente sí le correspondan.

## **7. Estructura técnica recomendada en Django**

Te propongo desarrollar un proyecto modular. Así no tendremos todo el código mezclado en una sola aplicación.

**Proyecto: encontrapp/**

Estructura propuesta del proyecto Django

```

encontrapp/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── profiles/
│   ├── publications/
│   ├── categories/
│   ├── locations/
│   ├── search/
│   ├── matches/
│   ├── conversations/
│   ├── recoveries/
│   ├── payments/
│   ├── notifications/
│   ├── favorites/
│   ├── reports/
│   ├── moderation/
│   ├── audit/
│   └── core/
│
├── templates/
├── static/
├── media/
├── requirements.txt
└── manage.py
  
```

### **¿Qué hará cada aplicación?**

| Aplicación      | Responsabilidad                                  |
| --------------- | ------------------------------------------------ |
| `accounts`      | Registro, login, permisos y cuentas              |
| `profiles`      | Información del perfil                           |
| `publications`  | Objetos perdidos y encontrados                   |
| `categories`    | Categorías de objetos                            |
| `locations`     | Departamentos, municipios y zonas                |
| `search`        | Búsqueda y filtros                               |
| `matches`       | Coincidencias automáticas                        |
| `conversations` | Chat y mensajes                                  |
| `recoveries`    | Solicitudes y entregas                           |
| `payments`      | QR, comprobantes y pagos                         |
| `notifications` | Avisos a usuarios                                |
| `favorites`     | Publicaciones guardadas                          |
| `reports`       | Denuncias                                        |
| `moderation`    | Revisión y sanciones                             |
| `audit`         | Registro de operaciones importantes              |
| `core`          | Inicio, páginas públicas y configuración general |

### **Modelos principales de la base de datos**

Estos son los modelos que necesitaremos diseñar:

- `User`: cuenta de usuario y tipo de acceso.
- `Profile`: datos públicos y preferencias del usuario.
- `Category`: categorías de objetos.
- `Publication`: publicación perdida o encontrada.
- `PublicationImage`: fotografías.
- `Location`: ubicación aproximada.
- `Match`: coincidencia entre dos publicaciones.
- `Conversation`: conversación entre usuarios.
- `Message`: mensajes.
- `RecoveryRequest`: solicitud de recuperación.
- `DeliveryConfirmation`: confirmaciones de entrega.
- `Dispute`: disputas.
- `Payment`: pagos.
- `PaymentProof`: comprobantes.
- `Notification`: notificaciones.
- `Favorite`: publicaciones favoritas.
- `Report`: denuncias.
- `BlockedUser`: bloqueos.
- `AuditLog`: auditoría.
- `LegalAcceptance`: aceptación de documentos legales.

Relaciones principales:

\#chatgpt-mermaid-\_r_1bf\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_1bf\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_1bf\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_1bf\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_1bf\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1bf\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_1bf\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_1bf\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_1bf\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_1bf\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_1bf\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_1bf\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1bf\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_1bf\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_1bf\_ p{margin:0;}#chatgpt-mermaid-\_r_1bf\_ .entityBox{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_1bf\_ .relationshipLabelBox{fill:rgb(48, 48, 48);opacity:0.7;background-color:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_1bf\_ .relationshipLabelBox rect{opacity:0.5;}#chatgpt-mermaid-\_r_1bf\_ .labelBkg{background-color:rgba(48, 48, 48, 0.5);}#chatgpt-mermaid-\_r_1bf\_ .edgeLabel{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_1bf\_ .edgeLabel .label rect{fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_1bf\_ .edgeLabel .label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1bf\_ .edgeLabel .label{fill:rgb(31, 78, 148);font-size:14px;}#chatgpt-mermaid-\_r_1bf\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_1bf\_ .edge-pattern-dashed{stroke-dasharray:8,8;}#chatgpt-mermaid-\_r_1bf\_ .node rect,#chatgpt-mermaid-\_r_1bf\_ .node circle,#chatgpt-mermaid-\_r_1bf\_ .node ellipse,#chatgpt-mermaid-\_r_1bf\_ .node polygon{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_1bf\_ .relationshipLine{stroke:rgb(175, 175, 175);stroke-width:1px;fill:none;}#chatgpt-mermaid-\_r_1bf\_ .marker{fill:none!important;stroke:rgb(175, 175, 175)!important;stroke-width:1;}#chatgpt-mermaid-\_r_1bf\_ [data-look=neo].labelBkg{background-color:rgba(48, 48, 48, 0.5);}#chatgpt-mermaid-\_r_1bf\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_1bf\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_1bf\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_1bf\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_1bf\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1bf\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_1bf\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_1bf\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}USERPROFILEPUBLICATIONCATEGORYPUBLICATION_IMAGEMATCHCONVERSATIONMESSAGERECOVERY_REQUESTDELIVERY_CONFIRMATIONPAYMENTDISPUTENOTIFICATIONREPORTtienecreaclasificacontieneparticipaparticipacontienereciberegistragenerapuede_tenerrecibepresenta

Una decisión de diseño: el usuario no tendrá que elegir permanentemente entre ser quien encuentra o quien busca. El tipo de publicación indicará si es un objeto perdido o encontrado. El rol de administrador sí estará separado y tendrá permisos especiales.

## **8. Diseño de las pantallas**

La página debe ser sencilla y transmitir confianza, no parecer un sistema administrativo.

[MVP for a lost & found app by Sudhanshu Soni](https://images.openai.com/static-rsc-4/slCiEEKop8-2HglA_AoslxgTWdbnfRlDynOm56A3Bht066aO3QhQUgdrNC0IOIEZuqfuwfmuCSEcD4I6TOLuV_-cHIiZKZmvgylQ1DKHC5JfCsnXyowMlJ6Ci5oi0GHVTqdD5OwIWJeaSzbpzitZYC9WSO4rY2ejiydWpWcd12k?purpose=inline)

**1. Inicio**

Buscador principal, botones para publicar objeto perdido o encontrado, publicaciones recientes y explicación del servicio.

[CampusFind | Devpost](https://images.openai.com/static-rsc-4/3fE7Zf4dDiA9P_rRA7993gIbTwCVslWaxn0Rf5FIXV7XhPR_neZ69AAJrY04JTnvfwVZugI17iE7LIBRKjydkrNG0m8-PzVuyrKUEvHe4o5kEmMkD8GAVxUIXGxlDRU760g2rpefIDoHWLmAzE4uQZV1nfoQuBM8N4H3xOFh2Xc?purpose=inline)

**2. Publicaciones**

Tarjetas con fotografía, categoría, descripción breve, fecha y ubicación aproximada.

[Direct Message UI by byrerobie galvez on Dribbble](https://images.openai.com/static-rsc-4/nMMVXit-ldj4zvd_Up-wjZO2U1FZuGnx4fSvaoc50fu8l35l_ThpQU3grZYZDjROKPfHv-Cy4Zj4gckejkrtLzMRreX8oYwaG0psW1VVC4G6Frio3KFYHGCx4uOk1V_cPw8fa73Vwiul3xjp70_xBVSn2OoGX7SoJhuYCHMxfdY?purpose=inline)

**3. Chat**

Lista de conversaciones, mensajes, fotografías y acceso a la publicación relacionada.

[Profile Dashboard Design :: Behance](https://images.openai.com/static-rsc-4/pj9I2c8OOp0iZNdTvw5WRU77PMR_f5vGOKxOP2xxpZ_kuFYbzLcLpQwCVrnevOgGX9ZFwYEDrXzbCsuZo0vAiARA3d6W4IXqu3COcA8NW5YuOlSr5NPKEHd-GZ-4Ga0bNOvlvdFiweYCaCn61d84FEsmX0p7vP2_3TSwYM3-kVg?purpose=inline)

**4. Mi cuenta**

Perfil, publicaciones, favoritos, solicitudes, recuperaciones y pagos.

[Gentelella — The free admin dashboard template, redesigned for 2026](https://images.openai.com/static-rsc-4/hQKnXOc8ILJjpVvxQxeI7dww1NsfJLZ43A0ja_G2WiZnaMTJalxK8Ocr4udr5dy-z1TEJss1OKFI_nceG9NF8vXpL3oHkvBEz0a-M6Sp2-rYZPG2RdmXFip2yPsW8pCpllo4B_MLd1NgrfAS-clB_Pz7exA0oH_15kjhc_-d7r0?purpose=inline)

**5. Administración**

Panel separado con estadísticas, usuarios, publicaciones, denuncias, pagos y configuración.

## **9. Tecnologías que utilizaremos**

| Parte                     | Tecnología                         |
| ------------------------- | ---------------------------------- |
| Backend                   | Django 5.2                         |
| Base de datos             | PostgreSQL                         |
| Frontend                  | HTML, CSS, JavaScript              |
| Diseño adaptable          | Bootstrap                          |
| Chat en tiempo real       | Django Channels                    |
| Comunicación              | WebSockets                         |
| Mapas                     | Leaflet + OpenStreetMap            |
| Procesamiento de imágenes | Pillow                             |
| Notificaciones            | Django + Web Push posteriormente   |
| Servidor                  | Ubuntu + Nginx + Gunicorn/Uvicorn  |
| Seguridad                 | HTTPS, firewall y controles Django |

No necesitamos Flutter ahora. Toda la interfaz estará construida para funcionar en computadora y celular. Más adelante podemos convertirla en PWA y, si tiene sentido, desarrollar una aplicación móvil.

## **10. Orden en el que desarrollaremos los módulos**

Aunque he listado todas las funciones, recomiendo implementar el sistema en este orden para que cada parte se pueda probar antes de avanzar.

**Plan de desarrollo**

# **0/43**

0% de tareas marcadas

**Fase 1 — Base del proyecto**

Crear proyecto Django y PostgreSQL

Configurar estructura modular

Crear diseño general y navegación

Crear cuentas y permisos

Crear perfiles

Implementar documentos legales y aceptación

**Fase 2 — Publicaciones**

Crear categorías

Crear ubicaciones

Publicar objetos perdidos

Publicar objetos encontrados

Subir y proteger fotografías

Editar, cerrar y consultar publicaciones

**Fase 3 — Búsqueda y coincidencias**

Buscador

Filtros

Favoritos

Comparación de publicaciones

Avisos de coincidencias

**Fase 4 — Comunicación**

Crear conversaciones

Enviar mensajes

Compartir imágenes

Notificaciones de mensajes

Bloquear y reportar usuarios

**Fase 5 — Recuperaciones**

Solicitudes de recuperación

Verificación de propiedad

Acuerdos de entrega

Confirmación de ambas partes

Disputas y cancelaciones

**Fase 6 — Pagos**

Configurar QR estático

Configurar tarifas

Adjuntar comprobantes

Verificación manual

Historial y reportes de pagos

**Fase 7 — Administración**

Panel administrativo propio

Gestión de usuarios y publicaciones

Denuncias y moderación

Auditoría

Estadísticas y reportes

**Fase 8 — Lanzamiento y pruebas**

Pruebas de seguridad y permisos

Pruebas de chat y pagos

Revisión legal y tributaria

Configurar dominio y HTTPS

Copias de seguridad

Prueba piloto con usuarios reales

Reiniciar checklist

## **11. Qué considero obligatorio antes de abrir al público**

No lanzaría EncontrApp sin comprobar, como mínimo, estos puntos:

- Registro, autenticación y permisos seguros.
- Publicaciones y fotografías protegidas.
- Chat privado con controles de acceso.
- Sistema para reportar y bloquear.
- Verificación de propiedad antes de una entrega.
- Proceso de recuperación y disputas.
- Verificación manual de pagos.
- Política de privacidad y términos publicados.
- Identificación del responsable y contacto de soporte.
- HTTPS y copias de seguridad.
- Pruebas de acceso indebido y vulnerabilidades.
- Revisión legal y tributaria antes de cobrar.

**Mi recomendación final:** construyamos EncontrApp como un servicio gratuito para publicar, buscar y conversar. El posible cobro por recuperación debe estar separado, ser transparente y no impedir que una persona utilice las funciones esenciales. Así será más fácil conseguir usuarios y generar confianza.

El primer paso de programación será crear el proyecto Django, PostgreSQL y las aplicaciones `accounts`, `profiles` y `core`. Después construiremos el registro y los permisos antes de comenzar con las publicaciones.



# **Product Backlog – EncontrApp**

**Proyecto:** EncontrApp\
**Tipo:** Plataforma web para publicar, buscar y recuperar objetos perdidos y encontrados.\
**Metodología:** Scrum\
**Backend:** Django\
**Frontend:** HTML, CSS, JavaScript y Bootstrap\
**Base de datos:** PostgreSQL\
**Usuarios:** Administrador, persona que encuentra y persona que busca.

El siguiente Product Backlog contiene las funcionalidades que desarrollaremos, organizadas por módulos y prioridades.

## **1. Criterios de prioridad**

- **P0 – Crítica:** indispensable para el funcionamiento y lanzamiento.
- **P1 – Alta:** importante para completar el servicio.
- **P2 – Media:** mejora la experiencia y administración.
- **P3 – Baja:** funcionalidad que puede incorporarse posteriormente.

## **2. Product Backlog general**

Historias de usuario ordenadas por prioridad. Los puntos son estimaciones iniciales de esfuerzo, no horas.

| ID     | Historia de usuario                                                     | Prioridad | Puntos |
| ------ | ----------------------------------------------------------------------- | --------- | ------ |
| HU-001 | Como usuario, quiero registrarme para utilizar EncontrApp.              | P0        | 5      |
| HU-002 | Como usuario, quiero iniciar y cerrar sesión de forma segura.           | P0        | 3      |
| HU-003 | Como usuario, quiero recuperar mi contraseña.                           | P0        | 3      |
| HU-004 | Como usuario, quiero verificar mi correo electrónico.                   | P0        | 3      |
| HU-005 | Como usuario, quiero administrar mi perfil.                             | P1        | 3      |
| HU-006 | Como administrador, quiero acceder a un panel exclusivo.                | P0        | 5      |
| HU-007 | Como administrador, quiero gestionar los permisos y roles.              | P0        | 5      |
| HU-008 | Como usuario, quiero aceptar los términos y la política de privacidad.  | P0        | 3      |
| HU-009 | Como usuario, quiero consultar las publicaciones disponibles.           | P0        | 5      |
| HU-010 | Como usuario, quiero registrar un objeto perdido.                       | P0        | 5      |
| HU-011 | Como usuario, quiero registrar un objeto encontrado.                    | P0        | 5      |
| HU-012 | Como usuario, quiero adjuntar fotografías a mis publicaciones.          | P0        | 5      |
| HU-013 | Como usuario, quiero editar mis publicaciones.                          | P1        | 3      |
| HU-014 | Como usuario, quiero cerrar o desactivar mis publicaciones.             | P0        | 3      |
| HU-015 | Como usuario, quiero consultar el detalle de una publicación.           | P0        | 3      |
| HU-016 | Como administrador, quiero gestionar las categorías.                    | P1        | 3      |
| HU-017 | Como administrador, quiero gestionar departamentos y municipios.        | P1        | 3      |
| HU-018 | Como usuario, quiero buscar objetos por palabras clave.                 | P0        | 5      |
| HU-019 | Como usuario, quiero filtrar objetos por categoría.                     | P0        | 3      |
| HU-020 | Como usuario, quiero filtrar por ubicación y fecha.                     | P1        | 5      |
| HU-021 | Como usuario, quiero ordenar las publicaciones por fecha.               | P2        | 2      |
| HU-022 | Como usuario, quiero guardar publicaciones favoritas.                   | P2        | 3      |
| HU-023 | Como usuario, quiero recibir sugerencias de objetos similares.          | P1        | 8      |
| HU-024 | Como usuario, quiero recibir alertas de posibles coincidencias.         | P1        | 5      |
| HU-025 | Como usuario, quiero consultar mis coincidencias.                       | P1        | 3      |
| HU-026 | Como usuario, quiero iniciar una conversación privada.                  | P0        | 5      |
| HU-027 | Como usuario, quiero enviar y recibir mensajes.                         | P0        | 5      |
| HU-028 | Como usuario, quiero compartir fotografías en el chat.                  | P1        | 3      |
| HU-029 | Como usuario, quiero recibir notificaciones de mensajes.                | P1        | 5      |
| HU-030 | Como usuario, quiero consultar mis conversaciones anteriores.           | P1        | 3      |
| HU-031 | Como usuario, quiero bloquear a otros usuarios.                         | P0        | 3      |
| HU-032 | Como usuario, quiero reportar conversaciones sospechosas.               | P0        | 3      |
| HU-033 | Como usuario, quiero solicitar la recuperación de un objeto.            | P0        | 5      |
| HU-034 | Como propietario, quiero demostrar que el objeto me pertenece.          | P0        | 5      |
| HU-035 | Como persona que encontró, quiero aceptar o rechazar una solicitud.     | P0        | 3      |
| HU-036 | Como usuarios, queremos acordar la entrega del objeto.                  | P0        | 3      |
| HU-037 | Como propietario, quiero confirmar que recibí el objeto.                | P0        | 3      |
| HU-038 | Como persona que encontró, quiero confirmar que entregué el objeto.     | P0        | 3      |
| HU-039 | Como usuario, quiero abrir una disputa cuando exista un problema.       | P1        | 5      |
| HU-040 | Como usuario, quiero consultar el historial de recuperaciones.          | P1        | 3      |
| HU-041 | Como usuario, quiero visualizar el QR para realizar un pago.            | P1        | 3      |
| HU-042 | Como usuario, quiero adjuntar mi comprobante de pago.                   | P1        | 3      |
| HU-043 | Como administrador, quiero verificar los pagos manualmente.             | P1        | 5      |
| HU-044 | Como usuario, quiero consultar el estado de mi pago.                    | P1        | 2      |
| HU-045 | Como administrador, quiero configurar las tarifas de recuperación.      | P1        | 3      |
| HU-046 | Como administrador, quiero gestionar las denuncias.                     | P0        | 5      |
| HU-047 | Como administrador, quiero suspender o bloquear usuarios.               | P0        | 3      |
| HU-048 | Como administrador, quiero moderar publicaciones.                       | P0        | 5      |
| HU-049 | Como administrador, quiero consultar estadísticas generales.            | P2        | 5      |
| HU-050 | Como administrador, quiero generar reportes de actividad y pagos.       | P2        | 5      |
| HU-051 | Como administrador, quiero consultar el registro de auditoría.          | P0        | 5      |
| HU-052 | Como usuario, quiero recibir notificaciones dentro de la plataforma.    | P1        | 5      |
| HU-053 | Como usuario, quiero solicitar la eliminación de mi cuenta.             | P0        | 3      |
| HU-054 | Como usuario, quiero consultar las preguntas frecuentes y ayuda.        | P2        | 2      |
| HU-055 | Como usuario, quiero utilizar la página desde mi celular o computadora. | P0        | 5      |

## **3. Backlog de seguridad y cumplimiento**

Estas historias son transversales: no pertenecen únicamente a un módulo, sino que deben desarrollarse junto con las funcionalidades correspondientes.

| ID      | Historia de usuario                                                             | Prioridad | Puntos |
| ------- | ------------------------------------------------------------------------------- | --------- | ------ |
| SEG-001 | Como usuario, quiero que mi contraseña se almacene de forma segura.             | P0        | 3      |
| SEG-002 | Como sistema, quiero validar los permisos en cada operación.                    | P0        | 5      |
| SEG-003 | Como usuario, quiero que mis datos personales no sean visibles públicamente.    | P0        | 5      |
| SEG-004 | Como sistema, quiero proteger los formularios contra ataques CSRF y XSS.        | P0        | 5      |
| SEG-005 | Como sistema, quiero validar las imágenes y archivos enviados.                  | P0        | 5      |
| SEG-006 | Como administrador, quiero consultar los registros de acciones importantes.     | P0        | 3      |
| SEG-007 | Como usuario, quiero que mis comunicaciones estén protegidas.                   | P0        | 5      |
| SEG-008 | Como administrador, quiero que existan copias de seguridad de la información.   | P0        | 3      |
| SEG-009 | Como usuario, quiero conocer cómo se utilizan mis datos personales.             | P0        | 3      |
| SEG-010 | Como administrador, quiero limitar los intentos de acceso y prevenir spam.      | P0        | 5      |
| SEG-011 | Como administrador, quiero realizar pruebas de seguridad antes del lanzamiento. | P0        | 5      |
| SEG-012 | Como usuario, quiero utilizar una conexión HTTPS segura.                        | P0        | 2      |

## **4. Organización por módulos y entregas**

| Entrega | Módulos                                 | Objetivo                                          |
| ------- | --------------------------------------- | ------------------------------------------------- |
| 1       | Cuentas, perfiles y permisos            | Tener usuarios registrados y accesos seguros      |
| 2       | Categorías, ubicaciones y publicaciones | Permitir registrar objetos perdidos y encontrados |
| 3       | Búsqueda y coincidencias                | Encontrar publicaciones relacionadas              |
| 4       | Chat y notificaciones                   | Permitir la comunicación entre usuarios           |
| 5       | Recuperaciones y entregas               | Gestionar el proceso de devolución                |
| 6       | Pagos con QR                            | Registrar y verificar pagos                       |
| 7       | Administración y moderación             | Controlar la plataforma                           |
| 8       | Seguridad, legal y despliegue           | Preparar la plataforma para su lanzamiento        |

## **5. Roles y responsabilidades**

| Funcionalidad              | Administrador                     | Encuentra       | Busca           |
| -------------------------- | --------------------------------- | --------------- | --------------- |
| Registrar cuenta           | Gestiona                          | Sí              | Sí              |
| Publicar objeto encontrado | No aplica                         | Sí              | Sí              |
| Publicar objeto perdido    | No aplica                         | Sí              | Sí              |
| Buscar publicaciones       | Sí                                | Sí              | Sí              |
| Consultar coincidencias    | Sí                                | Sí              | Sí              |
| Enviar mensajes            | Acceso limitado por procedimiento | Sí              | Sí              |
| Solicitar recuperación     | No                                | Puede recibir   | Sí              |
| Confirmar entrega          | No                                | Sí              | Sí              |
| Adjuntar comprobante       | No                                | Según el caso   | Según el caso   |
| Verificar pagos            | Sí                                | No              | No              |
| Gestionar usuarios         | Sí                                | No              | No              |
| Moderar publicaciones      | Sí                                | No              | No              |
| Gestionar denuncias        | Sí                                | Puede presentar | Puede presentar |

**Nota:** los roles de encuentra y busca son capacidades que cualquier cuenta puede utilizar. No deben convertirse en dos tipos de cuenta excluyentes.

## **6. Criterios de aceptación generales**

Para considerar terminada una historia de usuario, debe cumplir lo siguiente:

1. La funcionalidad trabaja correctamente.
2. Se valida la información ingresada.
3. Se muestran mensajes claros de éxito o error.
4. Se respetan los permisos de usuario.
5. Los datos se guardan correctamente en PostgreSQL.
6. Se adapta a celulares y computadoras cuando corresponda.
7. Se realizan pruebas de funcionamiento.
8. No se exponen datos privados.
9. Se registran las operaciones importantes cuando corresponde.

## **7. Primera versión: MVP**

Prioridad de lanzamiento

Para la primera versión funcional de EncontrApp recomiendo concentrarnos en estas capacidades:

- Registro e inicio de sesión.
- Perfiles y permisos.
- Publicaciones perdidas y encontradas.
- Fotografías.
- Categorías y ubicaciones.
- Buscador y filtros.
- Coincidencias básicas.
- Chat privado.
- Solicitudes de recuperación.
- Verificación de propiedad.
- Confirmación de entrega.
- Denuncias y bloqueos.
- Panel administrativo.
- Seguridad y documentos legales.
- Diseño adaptable.

Los pagos con QR pueden habilitarse después de validar el flujo de recuperación y definir las condiciones comerciales y legales.

## **8. Siguiente paso: comenzar el Sprint 1**

Mi propuesta es trabajar con sprints de dos semanas, revisando el resultado al terminar cada uno.

**Sprint 1 — Configuración y usuarios**

Primer sprint recomendado

**Objetivo:** tener la base del sistema y permitir que los usuarios creen sus cuentas de manera segura.

- HU-001 Registro de usuarios.
- HU-002 Inicio y cierre de sesión.
- HU-003 Recuperación de contraseña.
- HU-004 Verificación de correo.
- HU-006 Panel de administrador.
- HU-007 Permisos y roles.
- HU-008 Aceptación de términos.
- SEG-001 Seguridad de contraseñas.
- SEG-002 Control de permisos.

**Resultado esperado:** una web donde el administrador pueda ingresar y las personas puedan registrarse, iniciar sesión y administrar su cuenta.

**Recomendación:** este Product Backlog será nuestra lista principal de trabajo. Iremos marcando cada historia como pendiente, en desarrollo, en pruebas o terminada, sin comenzar el siguiente módulo hasta verificar el funcionamiento del anterior.