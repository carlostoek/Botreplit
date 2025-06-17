# Botmaestro

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure the environment. At a minimum the bot requires the Telegram token
   in `BOT_TOKEN`. Several optional variables control behaviour:

   ```bash
   export BOT_TOKEN="<your_bot_token>"
   export ADMIN_IDS="11111;22222"          # user IDs with admin privileges
   export VIP_CHANNEL_ID="-100123456789"   # ID of the VIP Telegram channel
   export FREE_CHANNEL_ID="-100987654321"  # ID of the free Telegram channel
   export DATABASE_URL="sqlite+aiosqlite:///gamification.db"  # DB connection
   export VIP_POINTS_MULTIPLIER="2"       # points multiplier for VIP members
   export CHANNEL_SCHEDULER_INTERVAL="30" # seconds between channel checks
   export VIP_SCHEDULER_INTERVAL="3600"   # seconds between VIP checks
   ```

   `DATABASE_URL` defaults to a local SQLite database. When running for the
   first time the bot will automatically create all tables.

## Environment variables

| Variable | Purpose |
| -------- | ------- |
| `BOT_TOKEN` | Telegram API token for the bot. **Required** |
| `ADMIN_IDS` | Semicolon separated list of Telegram user IDs that act as administrators |
| `VIP_CHANNEL_ID` | ID of the VIP Telegram channel. Users here are considered VIP |
| `FREE_CHANNEL_ID` | ID of the free access channel for non‑VIP users |
| `DATABASE_URL` | SQLAlchemy database URL. Defaults to `sqlite+aiosqlite:///gamification.db` |
| `VIP_POINTS_MULTIPLIER` | Points multiplier applied when a VIP user earns points |
| `CHANNEL_SCHEDULER_INTERVAL` | Seconds between checks for channel requests. Defaults to `30` |
| `VIP_SCHEDULER_INTERVAL` | Seconds between VIP subscription checks. Defaults to `3600` |
| `REACTION_BUTTONS` | Semicolon separated texts for reaction buttons used on channel posts |

### Customising reaction buttons

The emojis shown below channel posts can be changed at runtime. Open the admin
menu, choose **Configuración** and then **📝 Configurar Reacciones**. The bot
asks for each reaction emoji individually (up to ten). When finished, press
**Aceptar** to save the configuration.
You can also set initial values using the `REACTION_BUTTONS` environment
variable or by editing the `DEFAULT_REACTION_BUTTONS` list in
`mybot/utils/config.py`.

3. Initialise the database and populate base data (tables, achievements,
   levels and some starter missions). Run this command once after configuring
   the environment:

   ```bash
   python scripts/init_db.py
   ```

4. Run the bot locally:

   ```bash
   python mybot/bot.py
   ```

## Roles and flows

The bot distinguishes between three roles:

* **Admins** – IDs listed in `ADMIN_IDS` can manage channels and bot
  configuration using the admin menu.
* **VIP users** – users recognised as VIP by their membership of the VIP
  channel. VIPs get access to the full game, missions and rewards.
* **Free users** – anyone else interacting with the bot. They can request
  access to the free channel and have a simplified game experience.

### VIP flow

Users obtain VIP status via subscription tokens. Once activated they are added
to the VIP channel (if configured) and can open the menu with `/vip_menu` to
play the game, earn points and redeem rewards.

### Free flow

Non‑VIP users can request access to the free channel using the subscription
menu. Join requests are stored in the database and automatically approved once
the configured wait time has passed.

## Scheduler tasks

Two background loops run when the bot starts:

1. **Pending channel requests** – checks for free channel join requests and
   approves them after the wait time stored in the `bot_config` table.
2. **VIP subscription monitor** – sends expiry reminders 24&nbsp;hours before a
   VIP subscription ends and removes expired users from the VIP channel.
   The frequency of these checks can be changed at runtime from the admin
   panel or by setting `CHANNEL_SCHEDULER_INTERVAL` and
   `VIP_SCHEDULER_INTERVAL` environment variables.


## Estructura Lógica del Menú de Administración

Este proyecto está organizado mediante una interfaz de administración basada en menús jerárquicos, que estructuran las funcionalidades del bot de acuerdo a su propósito. Es fundamental respetar esta arquitectura lógica para garantizar coherencia, claridad y escalabilidad. A continuación, se describe cómo debe entenderse cada sección del menú:


---

🛠️ Menú Principal

Este es el panel de control general del bot. Aquí deben colocarse únicamente los accesos a funciones globales o nodos principales. No se deben colocar aquí botones o acciones específicas de gamificación ni de canales. Este menú contiene:

Acceso a la gestión de canales (VIP y free)

Acceso al módulo de juego (gamificación)

Configuraciones generales y de seguridad

Personalización de los textos de reacción que acompañan las publicaciones de canal

Sección de estadísticas del bot



---

🔐 Opción: Canal VIP 

Este submenú agrupa únicamente las funciones específicas para administrar el canal VIP. Las acciones que deben ir aquí incluyen:

Configuración del canal VIP (ID, invitaciones, acceso)

Planes de suscripción y tarifas

Visualización de usuarios VIP y expiraciones

Acciones administrativas aplicables solo al canal VIP


⚠️ No deben colocarse aquí funciones relacionadas con el canal Free ni con la gamificación.


---

🎁 Opción: Canal Free

Este submenú está dedicado exclusivamente a la configuración y gestión del canal gratuito. Las funciones típicas incluyen:

Registro del ID del canal Free

Control de accesos gratuitos o limitados

Configuración de contenido gratuito


⚠️ Este submenú no debe incluir botones del canal VIP ni funciones del sistema de juego.


---

🎮 Opción: Juego Kinky 

Este es el núcleo del sistema de gamificación y debe incluir todas las funciones relacionadas al sistema de juego, independientemente de cuántos canales haya.

Desde aquí se administra:

Reglas de gamificación global (puntos, niveles, logros, misiones)

Visualización y asignación de insignias

Competencias, rankings y lógica de progreso

Configuración de dinámicas del juego


🔁 Este módulo es transversal y puede impactar a usuarios de ambos canales (VIP y Free), pero su administración siempre se hace desde aquí.


---

🔒 Importante: No mezcles botones de un módulo en otro. El orden y ubicación correcta de los botones garantiza que el bot sea mantenible, escalable y fácil de entender para futuros desarrolladores y para Codex.


---

## Project structure

All active source code lives under the `mybot/` package. An earlier
`old_gamificacion` folder containing a legacy prototype has been removed
to avoid confusion.
