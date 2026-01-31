# commands/storage.py
from datetime import datetime
import os
from aiogram import Router, types
from aiogram.filters import Command

import config
from loader import backup_system, storage

router = Router()

@router.message(Command("mode_local"))
async def set_mode_local(message: types.Message):
    """Переключить на режим 'Только локально'"""
    if message.from_user.id == config.YOUR_USER_ID:
        if storage.switch_mode('local'):
            await message.answer("✅ Режим: Только локальное хранение")
        else:
            await message.answer("❌ Ошибка смены режима")

@router.message(Command("mode_cloud"))
async def set_mode_cloud(message: types.Message):
    """Переключить на режим 'Только облако'"""
    if message.from_user.id == config.YOUR_USER_ID:
        if storage.switch_mode('cloud'):
            await message.answer("✅ Режим: Только облачное хранение")
        else:
            await message.answer("❌ Ошибка смены режима")

@router.message(Command("mode_both"))
async def set_mode_both(message: types.Message):
    """Переключить на режим 'Локально + Облако'"""
    if message.from_user.id == config.YOUR_USER_ID:
        if storage.switch_mode('both'):
            await message.answer("✅ Режим: Локальное + облачное хранение")
        else:
            await message.answer("❌ Ошибка смены режима")

@router.message(Command("mode_mirror"))
async def set_mode_mirror(message: types.Message):
    """Переключить на режим 'Зеркалирование'"""
    if message.from_user.id == config.YOUR_USER_ID:
        if storage.switch_mode('mirror'):
            await message.answer("✅ Режим: Зеркалирование (файлы в обоих местах)")
        else:
            await message.answer("❌ Ошибка смены режима")


@router.message(Command("storage_mode"))
async def show_storage_mode(message: types.Message):
    """Показать текущий режим хранения"""
    if message.from_user.id != config.YOUR_USER_ID:
        await message.answer("❌ Только для администратора")
        return
    
    current = storage.get_current_mode()
    stats = storage.get_stats()
    
    response = (
        f"💾 **Текущий режим хранения:** {current['description']}\n\n"
        f"📊 **Статистика:**\n"
        f"• Всего файлов: {stats['total_files']}\n"
        f"• Локально: {stats['local']['file_count']} файлов\n"
    )
    
    await message.answer(response, parse_mode="Markdown")

@router.message(Command("cloud_status"))
async def cloud_status_cmd(message: types.Message):
    """Проверить статус облачного хранилища"""
    if message.from_user.id != config.YOUR_USER_ID:
        await message.answer("❌ Только для администратора")
        return
    
    current = storage.get_current_mode()
    stats = storage.get_stats()
    
    if storage.cloud is None:
        response = "☁️ **Облачное хранилище:** не настроено\n\n"
        response += "Чтобы настроить, добавьте в .env файл:\n"
        response += "```\n"
        response += "CLOUD_PROVIDER=s3  # или yandex, dropbox\n"
        response += "CLOUD_ACCESS_KEY=ваш_ключ\n"
        response += "CLOUD_SECRET_KEY=ваш_секрет\n"
        response += "CLOUD_BUCKET=имя_бакета\n"
        response += "```"
    else:
        response = (
            f"☁️ **Облачное хранилище:**\n"
            f"• Провайдер: {stats['cloud']['provider']}\n"
            f"• Статус: {stats['cloud'].get('status', 'активно')}\n"
            f"• Файлов: {stats['cloud']['file_count']}\n\n"
            f"💾 **Текущий режим:** {current['description']}\n"
            f"📊 **Всего файлов:** {stats['total_files']}\n"
        )
    
    await message.answer(response, parse_mode="Markdown")

@router.message(Command("backup_status"))
async def backup_status_cmd(message: types.Message):
    """Показать статус бэкапов"""
    if message.from_user.id != config.YOUR_USER_ID:
        await message.answer("❌ Только для администратора")
        return
    
    backup_dir = backup_system.backup_dir
    full_dir = os.path.join(backup_dir, "full")
    
    if not os.path.exists(full_dir):
        await message.answer("📦 Бэкапов еще нет")
        return
    
    backups = []
    for file in os.listdir(full_dir):
        if file.endswith('.zip'):
            file_path = os.path.join(full_dir, file)
            backups.append((file, os.path.getmtime(file_path)))
    
    if not backups:
        await message.answer("📦 Бэкапов еще нет")
        return
    
    # Сортируем по дате (новые сначала)
    backups.sort(key=lambda x: x[1], reverse=True)
    
    response = f"📦 **Последние бэкапы:** (всего {len(backups)})\n\n"
    
    for i, (backup_name, backup_time) in enumerate(backups[:5]):  # Показываем 5 последних
        time_str = datetime.fromtimestamp(backup_time).strftime("%d.%m.%Y %H:%M")
        file_path = os.path.join(full_dir, backup_name)
        size_mb = os.path.getsize(file_path) / 1024 / 1024 if os.path.exists(file_path) else 0
        
        response += f"{i+1}. **{backup_name}**\n"
        response += f"   📅 {time_str}\n"
        response += f"   📦 {size_mb:.1f} МБ\n\n"
    
    response += f"🔄 Авто-бэкапы: каждые {backup_system.backup_interval_days} дней\n"
    response += f"📁 Папка: {backup_dir}"  # ← ГЛАВНОЕ ИЗМЕНЕНИЕ: убрали кавычки

    await message.answer(response)

@router.message(Command("create_backup"))
async def create_backup_command(message: types.Message):
    """Обработчик команды /create_backup"""
    if message.from_user.id != config.CREATOR_ID:
        await message.answer("❌ Только для администратора")
        return
    
    await message.answer("🔄 Создаю резервную копию...")
    
    try:
        
        backup_info = await backup_system.create_backup("full")
        
        size_mb = backup_info['size'] / 1024 / 1024
        
        await message.answer(
            f"✅ **Резервная копия создана!**\n\n"
            f"📁 Имя: {backup_info['name']}\n"
            f"📦 Размер: {size_mb:.1f} МБ\n"
            f"⏰ Время: {backup_info['created_at']}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка создания бэкапа: {str(e)[:200]}")