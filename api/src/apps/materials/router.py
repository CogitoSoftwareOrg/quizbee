from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from .tokens_calculation import count_pdf_tokens
from apps.auth import User
from lib.clients import AdminPB
import asyncio

materials_router = APIRouter(prefix="/materials", tags=["materials"])


@materials_router.post("/upload")
async def upload_material(
    admin_pb: AdminPB,
    user: User,
    file: UploadFile = File(...),
    title: str = Form(...),
    material_id: str = Form(...)
):
    """
    Загружает материал в PocketBase с автоматическим подсчетом токенов для PDF файлов.
    """
    try:
        # Читаем содержимое файла
        file_bytes = await file.read()
        
        # Проверяем размер файла (лимит 30MB)
        file_size_mb = len(file_bytes) / (1024 * 1024)  # размер в мегабайтах
        max_size_mb = 30
        
        if file_size_mb > max_size_mb:
            # Файл слишком большой - создаем пустой объект со статусом 'too big'
            material_data = {
                'id': material_id,
                'title': title,
                'user': user.get("id"),
                'status': 'too big',
   
            }
            
            material = await admin_pb.collection("materials").create(material_data)
            
            return JSONResponse(content={
                "id": material.get("id"),
                "title": material.get("title"),
                "filename": file.filename,
                "status": "too big",
                "file_size_mb": round(file_size_mb, 2),
                "max_size_mb": max_size_mb,
                "success": False,
                "message": f"Файл слишком большой ({round(file_size_mb, 2)}MB). Максимальный размер: {max_size_mb}MB"
            })
        
        # Файл подходящего размера - обрабатываем как обычно
        material_data = {
            'id': material_id,
            'title': title,
            'user': user.get("id"),
            'file': (file.filename, file_bytes, file.content_type),
            'status': 'uploaded',

        }
        
        # Автоматически подсчитываем токены для PDF файлов
        token_count = None
        if file.filename and file.filename.lower().endswith('.pdf'):
            try:
                token_count = count_pdf_tokens(file_bytes)
                material_data['tokens'] = token_count
            except Exception as e:
                print(f"Error while counting tokens for {file.filename}: {e}")
        
        # Создаем материал в PocketBase
        material = await admin_pb.collection("materials").create(material_data)
        
        response_data = {
            "id": material.get("id"),
            "title": material.get("title"),
            "filename": file.filename,
            "status": "uploaded",
            "file_size_mb": round(file_size_mb, 2),
            "success": True,
            "message": "Материал успешно загружен"
        }
        
    
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке материала: {str(e)}"
        )


@materials_router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    admin_pb: AdminPB,
    user: User
):
    """
    Удаляет материал из PocketBase с проверкой прав доступа.
    """
    try:
        # Проверяем, что материал существует и принадлежит пользователю
        material = await admin_pb.collection("materials").get_one(material_id)
        
        if material.get("user") != user.get("id"):
            raise HTTPException(
                status_code=403,
                detail="У вас нет прав для удаления этого материала"
            )
        
        # Удаляем материал
        await admin_pb.collection("materials").delete(material_id)
        
     
        
        return JSONResponse(content={
            "success": True,
            "message": f"Материал '{material.get('title', 'Без названия')}' успешно удален"
        })
        
    except HTTPException:
       
        raise
    except Exception as e:
        print(f"Ошибка при удалении материала {material_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении материала: {str(e)}"
        )