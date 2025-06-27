
from __future__ import annotations

import logging
import random
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class LucienNotificationService:
    """Service for Lucien's gamified notifications with dark humor."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    # Paquete de 50 notificaciones de Lucien con humor ácido/negro
    LUCIEN_MESSAGES = [
        "🎭 *Otra reacción más... Qué originalidad la tuya*",
        "🔥 *Lucien nota que sigues aquí. Admirable persistencia o falta de vida social*",
        "💀 *¿Sabías que cada reacción te acerca más al siguiente nivel? También te acerca más a la muerte, pero bueno...*",
        "🎪 *Reaccionar es como aplaudir en un circo vacío. Pero hey, aquí tienes tu pista*",
        "🌙 *Lucien susurra: 'Cada click es una lágrima de productividad perdida'*",
        "⚡ *Dato curioso: El 73% de las reacciones son por aburrimiento. Tú decides en qué porcentaje estás*",
        "🎯 *Perfecto, otra víctima del sistema de gamificación. Lucien está orgulloso*",
        "💎 *¿Realmente crees que estos puntos valen algo? Lucien dice que sí, así que... síguele el juego*",
        "🎲 *La vida es una serie de clicks sin sentido. Al menos estos te dan recompensas*",
        "🔮 *Lucien predice tu futuro: más reacciones, más puntos, menos tiempo libre*",
        "🎭 *Actúas como si estos puntos fueran importantes. Plot twist: lo son*",
        "💀 *Cada reacción es un pequeño grito existencial. Lucien lo entiende*",
        "🌟 *Brillas más que tu pantalla a las 3 AM mientras juegas esto*",
        "🎪 *Bienvenido al circo digital donde tú eres el payaso y los puntos son cacahuates*",
        "🔥 *Tu dedicación es tan intensa que hasta Lucien se preocupa por tu salud mental*",
        "💫 *Dato absurdo: Los caracoles pueden dormir 3 años. Tú llevas 3 horas sin parar de jugar*",
        "🎯 *Lucien calculó que has gastado más energía en esto que en tus relaciones sociales*",
        "⚡ *Error 404: Vida social no encontrada. Pero hey, tienes puntos*",
        "🌙 *En una escala del 1 al 10, tu adicción a las reacciones es un sólido 11*",
        "💎 *Cada click es una pequeña traición a tu productividad. Lucien aprueba*",
        "🎲 *Probabilidad de que pares pronto: 12%. Probabilidad de que Lucien se ría de ti: 100%*",
        "🔮 *El oráculo dice: 'Seguirás reaccionando hasta que los servidores mueran'*",
        "🎭 *Tu persistencia es admirable. Tu criterio para elegir en qué gastar tiempo... cuestionable*",
        "💀 *Lucien lleva contando tus clicks. Van 47,892. No, es broma... o no*",
        "🌟 *Eres la estrella de tu propia comedia trágica digital*",
        "🎪 *Este es el espectáculo más triste que Lucien ha visto. Sigue así*",
        "🔥 *Tu historial de reacciones podría escribir una novela... una muy aburrida*",
        "💫 *Fact: Las medusas son inmortales. Tú actúas como si estos puntos también lo fueran*",
        "🎯 *Target acquired: Tu tiempo libre. Mission accomplished: Se acabó*",
        "⚡ *La energía que gastas aquí podría mover un molino. O cargar tu teléfono. Prioridades*",
        "🌙 *Son las {hora}. ¿Sabes dónde está tu productividad? Lucien sí: muerta*",
        "💎 *Cada punto que ganas es un pequeño paso hacia... absolutamente nada relevante*",
        "🎲 *Lanzaste los dados de la vida y salió 'adicción al gaming'. Crítico*",
        "🔮 *Visión del futuro: Tú, aquí mismo, en 5 años, todavía reaccionando*",
        "🎭 *Tu performance como jugador compulsivo merece un Oscar. O terapia*",
        "💀 *Dato morboso: Pasas más tiempo aquí que algunos cadáveres en el cementerio*",
        "🌟 *Brillas con la luz artificial de tu pantalla. Qué romántico*",
        "🎪 *Lucien presenta: El circo de la procrastinación. Tú eres la atracción principal*",
        "🔥 *Tu pasión por los puntos virtuales quema más que el infierno de Dante*",
        "💫 *Fun fact: Los pandas duermen 14 horas. Tú llevas 14 horas despierto jugando*",
        "🎯 *Misión cumplida: Has convertido el ocio en trabajo no remunerado*",
        "⚡ *Tu velocidad de reacción impresiona. Tu velocidad para hacer cosas útiles... no tanto*",
        "🌙 *Lucien está celoso de la atención que le das a este juego*",
        "💎 *Eres un diamante en bruto. Muy bruto. Pero diamante al fin*",
        "🎲 *RNG de la vida: 99% probabilidad de seguir jugando, 1% de hacer algo productivo*",
        "🔮 *El cristal muestra tu futuro: más de lo mismo, pero con más puntos*",
        "🎭 *Tu actuación como persona funcional es convincente. Lástima que solo sea actuación*",
        "💀 *Epitafio: 'Aquí yace alguien que convirtió clicking en arte'*",
        "🌟 *Eres la supernova de la procrastinación. Brillante pero destructiva*",
        "🎪 *Final del show: Lucien aplaude tu dedicación y llora por tu agenda*"
    ]
    
    def get_random_notification(self) -> str:
        """Get a random Lucien notification message."""
        return random.choice(self.LUCIEN_MESSAGES)
    
    async def send_reaction_notification(self, bot, user_id: int, points_earned: int = 0) -> bool:
        """Send a gamified notification when user reacts."""
        try:
            message = self.get_random_notification()
            
            if points_earned > 0:
                message += f"\n\n💰 *+{points_earned} besitos ganados*"
            
            await bot.send_message(
                user_id,
                message,
                parse_mode="Markdown"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending Lucien notification to {user_id}: {e}")
            return False
