from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_tarifas_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Nueva Tarifa", callback_data="tarifa_new")
    builder.button(text="🔙 Volver", callback_data="vip_config")
    builder.adjust(1)
    return builder.as_markup()


def get_duration_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="1 D\u00eda", callback_data="plan_dur_1")
    builder.button(text="2 D\u00edas", callback_data="plan_dur_2")
    builder.button(text="1 Semana", callback_data="plan_dur_7")
    builder.button(text="2 Semanas", callback_data="plan_dur_14")
    builder.button(text="1 Mes", callback_data="plan_dur_30")
    builder.adjust(2)
    return builder.as_markup()


def get_plan_list_kb(plans):
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.button(text=plan.name, callback_data=f"plan_link_{plan.id}")
    builder.adjust(1)
    return builder.as_markup()
