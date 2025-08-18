import json, asyncio, logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Message, ReplyKeyboardRemove,
    ReplyKeyboardMarkup, KeyboardButton
)
from sqlalchemy.ext.asyncio import AsyncSession
from .config import settings
from .db import add_subscriber, all_subscribers, remove_subscriber, ExchangeRequest

router = Router()
log = logging.getLogger(__name__)

def kb_main_inline() -> InlineKeyboardMarkup:
    v = "59"  # поднимай при обновлениях фронта, чтобы сбивать кэш WebView
    base = settings.webapp_base_url.rstrip("/")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧮 Калькулятор",  web_app=WebAppInfo(url=f"{base}/index.html?v={v}"))],
        [InlineKeyboardButton(text="📊 Табло курсов", web_app=WebAppInfo(url=f"{base}/rates.html?v={v}"))],
        [InlineKeyboardButton(text="🧪 Тест WebApp",  web_app=WebAppInfo(url=f"{base}/test.html?v={v}"))],
        [InlineKeyboardButton(text="💬 Чат", url="https://t.me/poizchat")],
        [InlineKeyboardButton(text="📞 Связаться с админом", url="https://t.me/poizmanager")],
    ])

def kb_main_reply() -> ReplyKeyboardMarkup:
    v = "24"
    base = settings.webapp_base_url.rstrip("/")
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧮 Калькулятор", web_app=WebAppInfo(url=f"{base}/index.html?v={v}"))],
            [KeyboardButton(text="📊 Табло курсов", web_app=WebAppInfo(url=f"{base}/rates.html?v={v}"))],
            [KeyboardButton(text="🧪 Тест WebApp", web_app=WebAppInfo(url=f"{base}/test.html?v={v}"))],
        ],
        resize_keyboard=True, one_time_keyboard=False
    )

# ===== Команды =====

@router.message(Command("start"))
async def cmd_start(m: types.Message, session: AsyncSession):
    await add_subscriber(session, m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer("Обновляю меню…", reply_markup=ReplyKeyboardRemove())
    await m.answer("Привет! Это Poiz Exchange 👋\nВыберите раздел:", reply_markup=kb_main_inline())

@router.message(Command("menu"))
async def cmd_menu(m: types.Message):
    await m.answer("Меню (inline) обновлено ✅", reply_markup=ReplyKeyboardRemove())
    await m.answer("Выберите раздел:", reply_markup=kb_main_inline())

@router.message(Command("menu_reply"))
async def cmd_menu_reply(m: types.Message):
    await m.answer("Меню (reply-кнопки) готово ✅\nНажмите нужную кнопку ниже.", reply_markup=kb_main_reply())

@router.message(Command("debug_links"))
async def cmd_debug_links(m: types.Message):
    v = "16"
    base = settings.webapp_base_url.rstrip("/")
    await m.answer(
        "Текущие ссылки WebApp:\n"
        f"🧮 {base}/index.html?v={v}\n"
        f"📊 {base}/rates.html?v={v}\n"
        f"🧪 {base}/test.html?v={v}\n"
        f"(источник: .env → WEBAPP_BASE_URL)\n"
    )

@router.message(Command("test"))
async def cmd_test(m: types.Message):
    base = settings.webapp_base_url.rstrip("/")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔧 Открыть тестовый WebApp", web_app=WebAppInfo(url=f"{base}/test.html?v=16"))
    ]])
    await m.answer("Открой и нажми «Отправить ping».", reply_markup=kb)

@router.message(Command("test_reply"))
async def cmd_test_reply(m: types.Message):
    base = settings.webapp_base_url.rstrip("/")
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔧 Тест WebApp (reply)", web_app=WebAppInfo(url=f"{base}/test.html?v=16"))]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await m.answer("Нажми зелёную кнопку ниже, затем «Отправить ping».", reply_markup=kb)

# ===== Приём данных из WebApp (sendData) =====

# Диагностический — поставлен ПЕРВЫМ по порядку, без БД
@router.message(F.web_app_data)
async def on_webapp_diag(m: Message):
    raw = getattr(m, "web_app_data", None)
    payload_txt = (raw.data if (raw and raw.data) else "")
    try:
        await m.answer("🟢 MIN: web_app_data получено")
        await m.answer(f"MIN RAW:\n{payload_txt[:2000]}")
    except Exception:
        pass

# Основной — сохраняет заявку и шлёт админу
@router.message(F.web_app_data)
async def on_webapp_request(m: Message, session: AsyncSession):
    raw = getattr(m, "web_app_data", None)
    payload_txt = (raw.data if (raw and raw.data) else "")

    # мгновенное подтверждение
    try:
        await m.answer("✅ Данные получены, обрабатываю…")
    except Exception:
        pass

    # парсим JSON
    try:
        data = json.loads(payload_txt) if payload_txt else {}
    except Exception as e:
        await m.answer("❌ Не смог прочитать JSON от WebApp.")
        await m.answer(f"RAW:\n{payload_txt[:1500]}")
        return

    # тестовый ping
    if data.get("action") == "ping":
        await m.answer("✅ Ping принят. tg.sendData работает.")
        return

    # заявка
    if data.get("action") != "request":
        await m.answer("⚠️ Пришли данные WebApp, но action != 'request'.")
        await m.answer(f"PAYLOAD:\n```{json.dumps(data, ensure_ascii=False, indent=2)}```", parse_mode="Markdown")
        return

    try:
        req = ExchangeRequest(
            user_id=m.from_user.id,
            username=m.from_user.username,
            direction=data.get("direction",""),
            amount_in=float(data.get("amount") or 0),
            contact=(data.get("contact") or ""),
            requisites=(data.get("requisites") or ""),
            note=(data.get("note") or ""),
        )
        session.add(req)
        await session.commit()

        await m.answer(f"🎉 Заявка #{req.id} принята. Менеджер свяжется с вами: @poizmanager")

        admin_chat = settings.admin_username.replace("@","")
        text = (
            f"🆕 Заявка #{req.id}\n"
            f"От: @{req.username or req.user_id}\n"
            f"Направление: {req.direction}\n"
            f"Сумма: {req.amount_in}\n"
            f"Контакт: {req.contact or '-'}\n"
            f"Реквизиты: {req.requisites or '-'}\n"
            f"Комментарий: {req.note or '-'}"
        )
        try:
            await m.bot.send_message(f"@{admin_chat}", text)
        except Exception as e:
            log.warning("Не удалось отправить админу: %s", e)

    except Exception as e:
        await m.answer("❌ Не удалось сохранить заявку. Напишите @poizmanager.")
        await m.answer(f"ERROR: {e!r}")

# ===== Рассылка (только для admin_username) =====
BROADCAST_STATE: dict[int, bool] = {}

@router.message(Command("sendall"))
async def sendall_start(m: types.Message, session: AsyncSession):
    if ("@" + (m.from_user.username or "")) != settings.admin_username:
        await m.answer("⛔ Команда только для администратора.")
        return
    BROADCAST_STATE[m.from_user.id] = True
    await m.answer("📣 Пришлите одно сообщение для рассылки (текст/фото/видео/документ с подписью).")

@router.message(F.from_user.id.func(lambda uid: BROADCAST_STATE.get(uid, False)))
async def sendall_collect(m: types.Message, session: AsyncSession):
    admin_id = m.from_user.id
    BROADCAST_STATE.pop(admin_id, None)

    subs_rows = await all_subscribers(session)
    subs = [row.id for row in subs_rows]
    await m.answer(f"🚀 Отправляю {len(subs)} подписчикам...")

    sent, removed = 0, 0
    for chat_id in subs:
        try:
            await m.copy_to(chat_id=chat_id)
            sent += 1
        except Exception:
            await remove_subscriber(session, chat_id)
            removed += 1
        await asyncio.sleep(0.05)

    await m.answer(f"✅ Готово. Отправлено: {sent}. Удалено из базы: {removed}.")

# ===== Отладочный перехватчик — СТРОГО ПОСЛЕДНИМ и не ловит команды =====
@router.message(F.text & ~F.text.startswith("/"))
async def catch_all(m: types.Message):
    await m.answer(f"DEBUG: content_type={m.content_type}")
