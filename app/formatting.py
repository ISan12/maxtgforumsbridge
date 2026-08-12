from html import escape


def h(text: str | None) -> str:
    return escape(text or "", quote=False)


def chat_message(name: str, text: str, is_group: bool = False) -> str:
    name = h(name)
    text = h(text)

    if is_group:
        return f"👤 <b>{name}</b>\n{text}"

    return text


def startup() -> str:
    return (
        "🟢 <b>maxtgforumsbridge запущен</b>\n\n"
        "MAX подключён, Telegram тоже на связи.\n"
        "Напиши /help, если забыл команды."
    )


def restart() -> str:
    return (
        "🔄 <b>maxtgforumsbridge перезапущен</b>\n\n"
        "Подключение восстановлено. Сохранённые чаты загружены."
    )


def service_title() -> str:
    return "📢 Bridge"


def send_notice(name: str, text: str) -> str:
    return (
        "📨 <b>Сообщение отправлено</b>\n\n"
        f"<b>Кому:</b> {h(name)}\n"
        f"<b>Текст:</b>\n{h(text)}"
    )


def delivered_notice(text: str) -> str:
    return (
        "📢 <b>Это системное сообщение</b>\n\n"
        "Сообщение доставлено пользователю. "
        "Ответ появится здесь, как только он ответит.\n\n"
        f"<b>Сообщение:</b>\n{h(text)}"
    )


def attachment_notice(kind: str, caption: str = "") -> str:
    suffix = f"\n{h(caption)}" if caption else ""
    return f"{kind}{suffix}"


def help_text() -> str:
    return (
        "🛠 <b>Команды</b>\n\n"
        "<code>/status</code> — состояние bridge\n"
        "<code>/send +79990000000 текст</code> — написать первым\n"
        "<code>/join https://max.ru/...</code> — вступить в MAX-группу\n"
        "<code>/help</code> — показать эту справку"
    )


def status_text(forum_id: int, service_topic: str | int | None) -> str:
    return (
        "🟢 <b>Bridge работает</b>\n\n"
        "MAX: <b>подключён</b>\n"
        "Telegram: <b>подключён</b>\n"
        f"Forum: <code>{forum_id}</code>\n"
        f"Служебная тема: <code>{service_topic or '—'}</code>"
    )
