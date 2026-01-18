from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user import User

async def create_user_account(data, session, background_tasks):
    
    user_exist = session.query(User).filter(User.emails == data.email).first()
    if user_exist:
        raise HTTPException(status_code=400, detail="Email is already exists.")
    
    if not is_password_strong_enough(data.password):
        raise HTTPException(status_code=400, detail="Please provide a strong password.")
    
    
    user = User()
    user.name = data.name
    user.email = data.email
    user.password = hash_password(data.password)
    
    session.add(user)
    session.commit()
    
    return user
