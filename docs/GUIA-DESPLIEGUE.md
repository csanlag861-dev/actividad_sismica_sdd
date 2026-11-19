# Tutorial paso a paso: despliegue del observatorio

Esta guía explica cómo publicar una **demostración accesible por Internet** con
los componentes que documenta este repositorio:

- Backend: Docker Compose ejecuta la API, PostgreSQL, Kafka, productor y
  consumidor en el ordenador donde se ejecutan los comandos.
- Frontend: Netlify publica la aplicación Angular.
- Conexión pública de prueba: ngrok crea un túnel HTTPS hacia la API local.

> **Importante:** este montaje no es un despliegue permanente de producción.
> Para que la demostración funcione, el ordenador debe permanecer encendido,
> Docker y ngrok deben seguir ejecutándose y debe haber conexión a Internet.
> El túnel de ngrok puede cambiar de dirección al reiniciarse. No publiques
> PostgreSQL ni Kafka. Solo se expone el puerto de la API.

Los comandos de esta guía son para **Windows PowerShell**. En VS Code, abre una
terminal PowerShell en la carpeta del proyecto. Si la terminal no está allí,
cambia a la carpeta donde clonaste el repositorio, por ejemplo:

```powershell
Set-Location "C:\ruta\a\actividad_sismica_sdd"
```

Comprueba que estás en la raíz: el comando siguiente debe devolver `True`.

```powershell
Test-Path .\compose.yaml
```

## 1. Instalar y comprobar los requisitos

Necesitas:

1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**,
   iniciado, con Docker Compose v2 disponible. En Windows, Docker Desktop debe
   tener habilitado su motor Linux/WSL 2 para ejecutar las imágenes del
   proyecto.
2. **[Node.js](https://nodejs.org/en/download): 22.12 o posterior dentro de la
   rama 22, o Node.js 24**, junto con npm. Se usa para probar y compilar el
   frontend localmente.
3. **[Git para Windows](https://git-scm.com/download/win)**, para obtener el
   código y conectarlo a Netlify.
4. Una cuenta de **[Netlify](https://app.netlify.com/signup)** y acceso a un
   repositorio Git propio al que Netlify pueda conectarse.
5. Una cuenta de **[ngrok](https://ngrok.com/)** para el túnel HTTPS de la
   demostración. La página de [descargas para Windows](https://ngrok.com/downloads/windows)
   ofrece el instalador.
6. Acceso a Internet para descargar imágenes y paquetes, consultar USGS y
   cargar los mapas base.

Abre PowerShell y comprueba qué herramientas están instaladas:

```powershell
docker --version
docker compose version
node --version
npm --version
git --version
```

Cada comando debe mostrar una versión y terminar sin error. Si falta alguno,
instálalo desde el sitio oficial de la herramienta y vuelve a comprobarlo.
Docker Desktop también debe estar abierto; que el comando `docker` exista no
significa necesariamente que el motor ya esté iniciado.

## 2. Obtener el proyecto

Si todavía no tienes una copia local, clona tu repositorio:

```powershell
git clone https://github.com/USUARIO/REPOSITORIO.git
Set-Location .\REPOSITORIO
```

Reemplaza `USUARIO/REPOSITORIO` por la dirección de tu propio repositorio. Si
partes del repositorio de clase y no tienes permiso para subir cambios, crea un
fork y conecta Netlify a ese fork. Si ya tienes el proyecto, cambia a su
carpeta raíz.

Verifica de nuevo que estás en el lugar correcto:

```powershell
Test-Path .\compose.yaml
Test-Path .\frontend\package.json
```

Ambos comandos deben devolver `True`.

## 3. Crear la configuración local del backend

El backend necesita una contraseña para PostgreSQL. Crea el archivo local
`.env` copiando la plantilla:

```powershell
Copy-Item .env.example .env
notepad .env
```

En el Bloc de notas, reemplaza el valor de `POSTGRES_PASSWORD` por una
contraseña aleatoria y única. Por ejemplo, puedes generar 32 caracteres
hexadecimales con este comando y copiar el resultado:

```powershell
[guid]::NewGuid().ToString("N")
```

No escribas los signos `<` o `>` alrededor del valor. Conserva las demás
variables de la plantilla, guarda `.env` y cierra el Bloc de notas. No subas
este archivo a Git, no lo pegues en Netlify y no lo incluyas en el frontend.
El `.gitignore` del proyecto excluye `.env`.

Comprueba la configuración de Compose antes de iniciar los servicios:

```powershell
docker compose config --quiet
```

Si no aparece un error, Compose ha podido leer la configuración. Si indica que
falta `POSTGRES_PASSWORD`, vuelve a revisar que guardaste `.env` en la raíz,
que el nombre del archivo no haya quedado como `.env.txt` y que la línea tenga
un valor después del signo `=`.

## 4. Iniciar y comprobar el backend

Desde la raíz del proyecto, descarga y construye las imágenes y arranca los
cinco servicios:

```powershell
docker compose up --build -d
```

La primera ejecución puede tardar mientras Docker descarga imágenes e instala
dependencias. Comprueba el estado:

```powershell
docker compose ps
```

Espera hasta que los servicios estén iniciados y sus comprobaciones de salud
estén correctas. Comprueba la API desde el propio ordenador:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/salud
Invoke-RestMethod http://127.0.0.1:8000/api/estadisticas
```

La primera URL comprueba la salud de la API; la segunda debe devolver
estadísticas en formato JSON. Si alguna orden falla, consulta los mensajes de
los servicios:

```powershell
docker compose logs --since 10m api consumidor productor kafka postgres
```

La primera consulta live a USGS comienza al iniciar el productor. Si quieres
añadir el conjunto histórico de 2025 a la demostración, ejecuta esta carga
opcional desde la raíz y espera a que termine:

```powershell
docker compose run --rm --no-deps productor python -m observatorio.producer.replay --year 2025 --min-magnitude 4 --event-type earthquake --interval-seconds 0
```

La carga puede tardar. Puedes observar el progreso y los errores con:

```powershell
docker compose logs --since 5m productor consumidor
```

No hace falta ejecutar la carga histórica para que el backend arranque.

## 5. Probar el frontend en local (recomendado)

Abre una **segunda terminal PowerShell**, manteniendo el backend activo en
Docker. Desde la raíz del proyecto, instala las dependencias exactamente como
las fija el archivo de bloqueo:

```powershell
Set-Location .\frontend
npm ci
```

Inicia el servidor de desarrollo:

```powershell
npm start
```

Deja esa terminal abierta y visita `http://localhost:4200` en el navegador. La
configuración local incluida apunta a `http://localhost:8000`, por lo que la
aplicación debería consultar el backend local. Para detener el servidor,
vuelve a la terminal y pulsa `Ctrl+C`.

Esta comprobación local no publica el frontend. El sitio público se construirá
y alojará en Netlify en los pasos siguientes.

## 6. Abrir un túnel HTTPS a la API con ngrok

Netlify no puede acceder a `localhost` de tu ordenador de forma directa. ngrok
proporciona una dirección HTTPS pública que reenvía las solicitudes al puerto
8000 local.

1. Instala ngrok. La opción recomendada por ngrok en Windows es Microsoft
   Store:

   ```powershell
   winget install ngrok -s msstore
   ```

   Si Windows pregunta si permites la instalación o que aceptes los términos,
   confirma para continuar. También puedes abrir la
   [ficha de ngrok en Microsoft Store](https://apps.microsoft.com/detail/9mvs1j51gmk6?utm_source=ngrok&utm_campaign=ngrok_downloads)
   e instalarlo desde allí. Cuando termine, cierra y vuelve a abrir PowerShell
   y comprueba la instalación:

   ```powershell
   ngrok version
   ```

   Si no tienes `winget` o no puedes usar Microsoft Store, descarga el ZIP
   oficial de
   [ngrok para Windows](https://ngrok.com/downloads/windows). En el Explorador
   de archivos, abre **Descargas**, haz clic derecho en el ZIP y selecciona
   **Extraer todo**. Indica como destino
   `C:\Users\TU_USUARIO\Downloads\ngrok`, sustituyendo `TU_USUARIO` por tu
   carpeta de usuario de Windows. Añade después esa carpeta, que debe contener
   `ngrok.exe`, al `PATH` de Windows. Como alternativa temporal, ejecuta en la
   misma terminal PowerShell:

   ```powershell
   $env:Path = "$env:USERPROFILE\Downloads\ngrok;$env:Path"
   ngrok version
   ```

   Esta modificación temporal solo afecta a esa terminal. Si `ngrok.exe` está
   en otra carpeta, cambia la ruta para que apunte a esa carpeta.

2. Crea una cuenta o inicia sesión en ngrok. En el
   [panel de ngrok](https://dashboard.ngrok.com/get-started/your-authtoken),
   copia el authtoken y regístralo localmente:

   ```powershell
   ngrok config add-authtoken "TU_AUTHTOKEN"
   ```

   Sustituye el texto de ejemplo por el token real. No lo compartas ni lo
   guardes en el repositorio o en el frontend; ngrok lo almacena en su
   configuración local.

3. Comprueba que Docker sigue publicando la API en
   `127.0.0.1:8000:8000` y abre el túnel:

   ```powershell
   ngrok http 8000
   ```

   En la salida, verifica que `Forwarding` termina en
   `-> http://localhost:8000`. Si muestra otro puerto, por ejemplo `8080`,
   pulsa `Ctrl+C` y vuelve a ejecutar `ngrok http 8000`.
4. Mantén esta terminal abierta. En la salida de ngrok, localiza la dirección
   `Forwarding` que comienza por `https://`, por ejemplo
   `https://ejemplo.ngrok-free.app`. Copia la dirección asignada a tu cuenta;
   el ejemplo no es una dirección real.
5. En una terminal PowerShell distinta, comprueba que la dirección llega a la
   ruta de salud de la API (no a la raíz del dominio):

   ```powershell
   Invoke-RestMethod https://TU-DOMINIO-NGROK/api/salud
   ```

   Sustituye `TU-DOMINIO-NGROK` por el dominio real, sin añadir texto de
   ejemplo. La llamada debe devolver la respuesta de salud de la API.

El token de ngrok es un secreto. No lo compartas, no lo pongas en
`frontend\public\config.json` y no lo guardes en `.env` del frontend.

## 7. Crear el sitio en Netlify

1. Inicia sesión en Netlify y elige la opción para añadir un sitio nuevo desde
   un proveedor Git.
2. Autoriza el acceso al proveedor y selecciona tu repositorio o fork.
3. En los ajustes de construcción, configura:

   | Ajuste | Valor |
   |---|---|
   | Base directory | `frontend` |
   | Build command | `npm run build` |
   | Publish directory | `dist/observatorio/browser` |

   La carpeta publicada es relativa a `frontend`. El archivo
   `frontend\netlify.toml` contiene el comando, la carpeta y la regla de
   redirección para las rutas de la SPA.
4. Inicia el despliegue y espera a que Netlify indique que la publicación ha
   terminado. Anota el dominio HTTPS asignado, por ejemplo
   `https://nombre-del-sitio.netlify.app`.

En este punto el sitio está publicado, pero todavía no se ha configurado para
consultar el backend público. Continúa con los dos pasos siguientes.

## 8. Permitir en la API el origen de Netlify

La API solo acepta el origen local de desarrollo de forma predeterminada. Para
permitir que la página publicada la consulte, añade el **origen exacto** del
sitio a `CORS_ALLOWED_ORIGINS` en `.env`.

Vuelve a una terminal situada en la raíz del proyecto y abre `.env`:

```powershell
notepad .env
```

Añade una línea como esta, sustituyendo el ejemplo por el dominio real de
Netlify:

```dotenv
CORS_ALLOWED_ORIGINS=https://nombre-del-sitio.netlify.app
```

Escribe solo el origen: debe comenzar por `https://` y no debe incluir una
ruta, una barra final, comodines ni credenciales. Si vas a usar más de un
dominio propio de Netlify, sepáralos con comas, sin espacios, por ejemplo:
`https://sitio.netlify.app,https://www.ejemplo.org`.

Guarda el archivo y recrea el contenedor de la API para que lea la nueva
configuración:

```powershell
docker compose up -d --force-recreate api
docker compose ps api
Invoke-RestMethod http://127.0.0.1:8000/api/salud
```

Espera a que la API vuelva a estar saludable. El túnel de ngrok debe seguir
abierto durante este cambio.

## 9. Configurar el frontend para usar la API pública

El archivo de configuración del frontend se sirve públicamente. No pongas en
él contraseñas, tokens ni otras credenciales. Actualiza el archivo con la URL
HTTPS real que asignó ngrok:

```powershell
notepad .\frontend\public\config.json
```

Déjalo con esta estructura, reemplazando el dominio de ejemplo:

```json
{
  "apiBaseUrl": "https://TU-DOMINIO-NGROK"
}
```

No añadas `/api` al final: la aplicación ya añade las rutas de API al valor de
`apiBaseUrl`. No uses `http://localhost:8000`: en una página publicada,
`localhost` se refiere al dispositivo de cada visitante, no al ordenador que
ejecuta Docker. Guarda el archivo.

Netlify necesita recibir el cambio para construir y publicar una versión nueva.
Desde la raíz, revisa los archivos modificados:

```powershell
git status --short
```

Confirma que `.env` **no** aparece en la lista. Sube el cambio público de
configuración a la rama conectada a Netlify:

```powershell
git add frontend/public/config.json
git commit -m "Configure public API URL"
git push
```

Si tu rama predeterminada tiene otro nombre o el repositorio no tiene un remoto
configurado, usa la rama/remoto que conectaste a Netlify. También puedes iniciar
una nueva publicación desde el panel de Netlify una vez que el cambio esté en
ese repositorio. Espera a que termine el nuevo build.

Antes de probar el panel, comprueba qué configuración se publicó:

```powershell
Invoke-RestMethod https://TU-SITIO-NETLIFY/config.json
```

La respuesta debe mostrar la URL HTTPS actual de ngrok en `apiBaseUrl`, no
`localhost`. Después comprueba que la propia API es accesible desde Internet:

```powershell
Invoke-RestMethod https://TU-DOMINIO-NGROK/api/salud
```

Debe devolver el estado de salud de la API. Si esta segunda llamada falla,
deja abierta la terminal de ngrok, comprueba que `Forwarding` apunta a
`http://localhost:8000` y revisa `http://127.0.0.1:4040` para saber si llegan
solicitudes al túnel.

## 10. Verificar el despliegue completo

1. Abre el dominio HTTPS de Netlify en el navegador.
2. Recarga la página y comprueba que se muestran datos del observatorio.
3. Navega a las vistas principales y confirma que la aplicación no se queda
   mostrando un error de conexión.
4. Si el navegador muestra un error de red, abre las herramientas de
   desarrollador del navegador, selecciona **Network/Red** y vuelve a cargar.
   Comprueba que las solicitudes a `apiBaseUrl` usan el dominio HTTPS ngrok y
   que las respuestas HTTP no son de error.
5. Si la API deja de responder, comprueba en sus terminales que Docker y ngrok
   siguen ejecutándose y revisa:

   ```powershell
   docker compose ps
   docker compose logs --since 10m api productor consumidor
   ```

La regla `_redirects` de Netlify está incluida para que las rutas de Angular
también funcionen al recargar directamente una URL del sitio.

## Problemas frecuentes

| Síntoma | Qué revisar |
|---|---|
| Compose dice que falta `POSTGRES_PASSWORD` | `.env` está en la raíz, se llama exactamente `.env` y contiene una contraseña. |
| Docker no puede conectarse al motor | Inicia Docker Desktop y espera a que termine de cargar. |
| El sitio funciona localmente pero no en Netlify | `config.json` debe usar la dirección HTTPS actual de ngrok, sin `/api`; después hay que publicar el cambio. |
| Netlify indica que no puede consultar la salud de la API | Abre `/config.json` en el dominio publicado: si `apiBaseUrl` es `localhost`, corrígelo y vuelve a publicar. Luego prueba `/api/salud` en el dominio ngrok desde otra terminal; si no responde, verifica que ngrok sigue abierto y reenvía a `localhost:8000`. |
| Error CORS en el navegador | `CORS_ALLOWED_ORIGINS` debe contener el origen exacto de Netlify (solo esquema y dominio) y la API debe haberse recreado. |
| El dominio ngrok ya no responde | El túnel se cerró o cambió de URL. Inícialo otra vez y actualiza `frontend\public\config.json`; publica el nuevo build. |
| Netlify no encuentra los archivos compilados | Revisa que la base sea `frontend` y la carpeta publicada `dist/observatorio/browser`. |
| El panel no muestra eventos inmediatamente | Comprueba la API y los logs del productor/consumidor; la fuente live se actualiza periódicamente. La carga histórica de 2025 es opcional. |

## Detener la demostración y conservar los datos

Para cerrar el túnel, pulsa `Ctrl+C` en la terminal de ngrok. Para detener los
servicios del backend sin borrar la base ni los archivos archivados:

```powershell
docker compose down
```

No uses `docker compose down -v` si quieres conservar los volúmenes de
PostgreSQL, Kafka y los archivos originales. Cuando vuelvas a iniciar Docker
Compose, los volúmenes se reutilizan.

## Alcance del despliegue

Netlify aloja el frontend, pero en este procedimiento la API, Kafka,
PostgreSQL y el pipeline siguen en tu ordenador. ngrok publica temporalmente la
API a Internet; no la convierte en un servicio siempre disponible. Para una
instalación permanente, habría que alojar los servicios backend en una
plataforma con persistencia, configurar su red y seguridad, y sustituir la URL
temporal de ngrok por una URL estable. Ese procedimiento no está cubierto por
la configuración documentada de este proyecto.

Para más detalle sobre variables, operación del productor, cargas históricas,
retención y migraciones, consulta [Operación del pipeline](./PIPELINE-OPERACION.md).
