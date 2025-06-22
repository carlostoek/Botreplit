# utils/messages.py
BOT_MESSAGES = {
    "start_welcome_new_user": (
        "🌙 Bienvenid@ a *El Diván de Diana*…\n\n"
        "Aquí cada gesto, cada decisión y cada paso que das, suma. Con cada interacción, te adentras más en *El Juego del Diván*.\n\n"
        "¿Estás list@ para descubrir lo que te espera? Elige por dónde empezar, yo me encargo de hacer que lo disfrutes."
    ),
    "start_welcome_returning_user": (
        "✨ Qué bueno tenerte de regreso.\n\n"
        "Tu lugar sigue aquí. Tus puntos también... y hay nuevas sorpresas esperándote.\n\n"
        "¿List@ para continuar *El Juego del Diván*?"
    ),
    "vip_members_only": "Esta sección está disponible solo para miembros VIP.",
    "profile_not_registered": "Parece que aún no has comenzado tu recorrido. Usa /start para dar tu primer paso.",
    "profile_title": "🛋️ *Tu rincón en El Diván de Diana*",
    "profile_points": "📌 *Puntos acumulados:* `{user_points}`",
    "profile_level": "🎯 *Nivel actual:* `{user_level}`",
    "profile_points_to_next_level": "📶 *Para el siguiente nivel:* `{points_needed}` más (Nivel `{next_level}` a partir de `{next_level_threshold}`)",
    "profile_max_level": "🌟 Has llegado al nivel más alto... y se nota. 😉",
    "profile_achievements_title": "🏅 *Logros desbloqueados*",
    "profile_no_achievements": "Aún no hay logros. Pero te tengo fe.",
    "profile_active_missions_title": "📋 *Tus desafíos activos*",
    "profile_no_active_missions": "Por ahora no hay desafíos, pero eso puede cambiar pronto. Mantente cerca.",
    "missions_title": "🎯 *Desafíos disponibles*",
    "missions_no_active": "No hay desafíos por el momento. Aprovecha para tomar aliento.",
    "mission_not_found": "Ese desafío no existe o ya expiró.",
    "mission_already_completed": "Ya lo completaste. Buen trabajo.",
    "mission_completed_success": "✅ ¡Desafío completado! Ganaste `{points_reward}` puntos.",
    "mission_completed_feedback": "🎉 ¡Misión '{mission_name}' completada! Ganaste `{points_reward}` puntos.",
    "mission_level_up_bonus": "🚀 Subiste de nivel. Ahora estás en el nivel `{user_level}`. Las cosas se pondrán más interesantes.",
    "mission_achievement_unlocked": "\n🏆 Logro desbloqueado: *{achievement_name}*",
    "mission_completion_failed": "❌ No pudimos registrar este desafío. Revisa si ya lo hiciste antes o si aún está activo.",
    "reward_shop_title": "🎁 *Recompensas del Diván*",
    "reward_shop_empty": "Por ahora no hay recompensas disponibles. Pero pronto sí. 😉",
    "reward_not_found": "Esa recompensa ya no está aquí... o aún no está lista.",
    "reward_not_registered": "Tu perfil no está activo. Usa /start para comenzar *El Juego del Diván*.",
    "reward_not_enough_points": "Te faltan `{required_points}` puntos. Ahora tienes `{user_points}`. Pero sigue... estás cerca.",
    "reward_claim_success": "🎉 ¡Recompensa reclamada!",
    "reward_claim_failed": "No pudimos procesar tu solicitud.",
    "reward_already_claimed": "Esta recompensa ya fue reclamada.",
    # Niveles
    "level_up_notification": "🎉 ¡Subiste a Nivel {level}: {level_name}! {reward}",
    "special_level_reward": "✨ Recompensa especial por alcanzar el nivel {level}! {reward}",
    # Mensajes de ranking (Unificados)
    "ranking_title": "🏆 *Tabla de Posiciones*",
    "ranking_entry": "#{rank}. @{username} - Puntos: `{points}`, Nivel: `{level}`",
    "no_ranking_data": "Aún no hay datos en el ranking. ¡Sé el primero en aparecer!",
    "back_to_main_menu": "Has regresado al centro del Diván. Elige por dónde seguir explorando.",
    # Botones
    "profile_achievements_button_text": "🏅 Mis Logros",
    "profile_active_missions_button_text": "🎯 Mis Desafíos",
    "back_to_profile_button_text": "← Volver a mi rincón",
    "view_all_missions_button_text": "Ver todos los desafíos",
    "back_to_missions_button_text": "← Volver a desafíos",
    "complete_mission_button_text": "✅ Completado",
    "confirm_purchase_button_text": "Canjear por `{cost}` puntos",
    "cancel_purchase_button_text": "❌ Cancelar",
    "back_to_rewards_button_text": "← Volver a recompensas",
    "prev_page_button_text": "← Anterior",
    "next_page_button_text": "Siguiente →",
    "back_to_main_menu_button_text": "← Volver al inicio",
    # Detalles
    "mission_details_text": (
        "🎯 *Desafío:* {mission_name}\n\n"
        "📖 *Descripción:* {mission_description}\n"
        "🎁 *Recompensa:* `{points_reward}` puntos\n"
        "⏱️ *Frecuencia:* `{mission_type}`"
    ),
    "reward_details_text": (
        "🎁 *Recompensa:* {reward_title}\n\n"
        "📌 *Descripción:* {reward_description}\n"
        "🔥 *Requiere:* `{required_points}` puntos"
    ),
    "reward_details_not_enough_points_alert": "💔 Te faltan puntos para esta recompensa. Necesitas `{required_points}`, tienes `{user_points}`. Sigue sumando, lo estás haciendo bien.",
    # Mensajes adicionales que eran mencionados en user_handlers.py
    "menu_missions_text": "Aquí están los desafíos que puedes emprender. ¡Cada uno te acerca más!",
    "menu_rewards_text": "¡Es hora de canjear tus puntos! Aquí tienes las recompensas disponibles:",
    "confirm_purchase_message": "¿Estás segur@ de que quieres canjear {reward_name} por {reward_cost} puntos?",
    "purchase_cancelled_message": "Compra cancelada. Puedes seguir explorando otras recompensas.",
    "gain_points_instructions": "Puedes ganar puntos completando misiones y participando en las actividades del canal.",
    "points_total_notification": "Tienes ahora {total_points} puntos acumulados.",
    "checkin_success": "✅ Check-in registrado. Ganaste {points} puntos.",
    "checkin_already_done": "Ya realizaste tu check-in. Vuelve mañana.",
    "daily_gift_received": "🎁 Recibiste {points} puntos del regalo diario!",
    "daily_gift_already": "Ya reclamaste el regalo diario. Vuelve mañana.",
    "daily_gift_disabled": "Regalos diarios deshabilitados.",
    "minigames_disabled": "Minijuegos deshabilitados.",
    "dice_points": "Ganaste {points} puntos lanzando el dado.",
    "trivia_correct": "¡Correcto! +5 puntos",
    "trivia_wrong": "Respuesta incorrecta.",
    "unrecognized_command_text": "Comando no reconocido. Aquí está el menú principal:",
    # Notificaciones de gamificación
    "challenge_completed": "🎯 ¡Desafío {challenge_type} completado! +{points} puntos",
    "reaction_registered": "👍 ¡Reacción registrada!",
    # --- Administración de Recompensas ---
    "enter_reward_name": "Ingresa el nombre de la recompensa:",
    "enter_reward_points": "¿Cuántos puntos se requieren?",
    "enter_reward_description": "Agrega una descripción (opcional):",
    "select_reward_type": "Selecciona el tipo de recompensa:",
    "reward_created": "✅ Recompensa creada.",
    "reward_deleted": "❌ Recompensa eliminada.",
    "reward_updated": "✅ Recompensa actualizada.",
    "invalid_number": "Ingresa un número válido.",
    "user_no_badges": "Aún no has desbloqueado ninguna insignia. ¡Sigue participando!",
    "level_created": "✅ Nivel creado correctamente.",
    "level_updated": "✅ Nivel actualizado.",
    "level_deleted": "❌ Nivel eliminado.",
    "FREE_MENU_TEXT": "✨ *Bienvenid@ a mi espacio gratuito*\n\nElige y descubre un poco de mi mundo...",
    "FREE_GIFT_TEXT": (
        "🎁 *Desbloquear regalo*\n"
        "Activa tu obsequio de bienvenida y descubre los primeros detalles de todo lo que tengo para ti."
    ),
    "PACKS_MENU_TEXT": (
        "🎀 *Paquetes especiales de Diana* 🎀\n\n"
        "¿Quieres una probadita de mis momentos más intensos?\n\n"
        "Estos son sets que puedes comprar directamente, sin suscripción. "
        "Cada uno incluye fotos y videos explícitos. 🥵\n\n"
        "🛍️ Elige tu favorito y presiona *“Me interesa”*. Yo me pondré en contacto contigo."
    ),
    "PACK_1_DETAILS": "💫 *Encanto Inicial – $150 MXN*\n\nFotos y videos perfectos para iniciar tu colección.",
    "PACK_2_DETAILS": "🔥 *Sensualidad Revelada – $200 MXN*\n\nUn nivel más de pasión en cada imagen.",
    "PACK_3_DETAILS": "💋 *Pasión Desbordante – $250 MXN*\n\nMis momentos más atrevidos capturados para ti.",
    "PACK_4_DETAILS": "🔞 *Intimidad Explosiva – $300 MXN*\n\nContenido explícito y sin censura.",
    "PACK_INTEREST_REPLY": "💌 ¡Gracias! Recibí tu interés. Me pondré en contacto contigo muy pronto. O si no quieres esperar escríbeme directo a mi chat privado en ,,@DianaKinky ",
    "FREE_VIP_EXPLORE_TEXT": (
        "🔐 *Explorar el canal VIP*\n"
        "Aquí comparto el contenido más atrevido y sorpresas solo para miembros. ¿Te unes?"
    ),
    "FREE_CUSTOM_TEXT": (
        "💌 *Quiero contenido personalizado*\n"
        "Cuéntame tus fantasías y recibirás algo hecho solo para ti."
    ),
    "FREE_GAME_TEXT": (
        "🎮 *Modo gratuito del juego Kinky*\n"
        "Disfruta de un adelanto de la diversión. La versión completa te espera en el VIP."
    ),
    "FREE_FOLLOW_TEXT": (
        "🌐 *¿Dónde más seguirme?*\n"
        "Encuentra todos mis enlaces y redes para que no te pierdas nada."
    ),
}

# Textos descriptivos para las insignias disponibles en el sistema.
# El identificador sirve como clave de referencia interna.
BADGE_TEXTS = {
    "first_message": {
        "name": "Primer Mensaje",
        "description": "Envía tu primer mensaje en el chat",
    },
    "conversador": {
        "name": "Conversador",
        "description": "Alcanza 100 mensajes enviados",
    },
    "invitador": {
        "name": "Invitador",
        "description": "Consigue 5 invitaciones exitosas",
    },
}

# Plantilla de mensaje para mostrar el nivel del usuario
NIVEL_TEMPLATE = """
🎮 Tu nivel actual: {current_level}
✨ Puntos totales: {points}
📊 Progreso hacia el siguiente nivel: {percentage:.1%}
🎯 Te faltan {points_needed} puntos para alcanzar el nivel {next_level}.
"""
