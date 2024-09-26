from sqlalchemy.orm import Session
from auth.models import User 
from cloudinary.uploader import upload
from cloudinary_config import cloudinary
import database
import fastapi

def update_user_avatar(user_id: int, avatar_file: bytes, db = fastapi.Depends(database.get_database)) -> str:
    """
    Updates the avatar of a user by uploading a new image to Cloudinary and saving the URL in the database.

    Args:
        user_id (int): The ID of the user whose avatar is being updated.
        avatar_file (bytes): The file content of the new avatar image in bytes.
        db (Session): Database session dependency.

    Returns:
        str: The URL of the newly uploaded avatar image.

    Raises:
        Exception: If the user with the provided ID is not found in the database.
    """
    response = upload(avatar_file, folder='avatars')
    avatar_url = response['secure_url']

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.avatar_url = avatar_url
        db.commit()
        return avatar_url
    else:
        raise Exception("User not found")
