"""
用户认证相关的API路由
Authentication API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

from ..models.schemas import APIResponse
from ..utils.response import success_response, error_response

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

# 配置
SECRET_KEY = "your-secret-key-change-in-production"  # 生产环境中应该使用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 用户数据文件路径（简单的文件存储，生产环境应使用数据库）
USERS_FILE = Path(__file__).parent.parent.parent / "database" / "users.json"

# 确保数据库目录存在
USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_users():
    """加载用户数据"""
    try:
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 创建默认管理员用户
            default_users = {
                "admin": {
                    "username": "admin",
                    "email": "admin@logistics.com",
                    "password_hash": hash_password("admin123"),
                    "role": "admin",
                    "created_at": datetime.now().isoformat(),
                    "is_active": True,
                    "last_login": None
                }
            }
            save_users(default_users)
            return default_users
    except Exception as e:
        logger.error(f"加载用户数据失败: {str(e)}")
        return {}

def save_users(users):
    """保存用户数据"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存用户数据失败: {str(e)}")

def hash_password(password: str) -> str:
    """密码哈希"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    try:
        salt, stored_hash = password_hash.split(':')
        password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return password_hash_check.hex() == stored_hash
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(username: str = Depends(verify_token)):
    """获取当前用户"""
    users = load_users()
    user = users.get(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )
    return user

@router.post("/login", response_model=APIResponse)
async def login(credentials: Dict[str, Any]):
    """
    用户登录
    """
    try:
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "")
        remember_me = credentials.get("rememberMe", False)

        if not username or not password:
            return error_response("用户名和密码不能为空")

        # 加载用户数据
        users = load_users()
        user = users.get(username)

        if not user:
            return error_response("用户名或密码错误")

        if not user.get("is_active", True):
            return error_response("账户已被禁用，请联系管理员")

        # 验证密码
        if not verify_password(password, user["password_hash"]):
            return error_response("用户名或密码错误")

        # 创建访问token
        access_token_expires = timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES * 24 if remember_me else ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        # 更新最后登录时间
        user["last_login"] = datetime.now().isoformat()
        users[username] = user
        save_users(users)

        # 返回用户信息（不包含密码哈希）
        user_info = {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user["created_at"],
            "last_login": user["last_login"],
            "token": access_token,
            "token_type": "bearer"
        }

        logger.info(f"用户 {username} 登录成功")
        return success_response(
            data=user_info,
            message="登录成功"
        )

    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        return error_response(f"登录失败: {str(e)}")

@router.post("/register", response_model=APIResponse)
async def register(user_data: Dict[str, Any]):
    """
    用户注册
    """
    try:
        username = user_data.get("username", "").strip()
        email = user_data.get("email", "").strip()
        password = user_data.get("password", "")
        role = user_data.get("role", "viewer")
        agree_terms = user_data.get("agreeTerms", False)

        # 基础验证
        if not username or not email or not password:
            return error_response("用户名、邮箱和密码不能为空")

        if not agree_terms:
            return error_response("请同意服务条款")

        # 验证用户名格式
        if len(username) < 3 or len(username) > 20:
            return error_response("用户名长度必须在3-20个字符之间")

        # 验证密码强度
        if len(password) < 8:
            return error_response("密码长度至少8个字符")

        # 验证邮箱格式（简单验证）
        if "@" not in email or "." not in email:
            return error_response("请输入有效的邮箱地址")

        # 加载现有用户数据
        users = load_users()

        # 检查用户名是否已存在
        if username in users:
            return error_response("用户名已存在")

        # 检查邮箱是否已存在
        for existing_user in users.values():
            if existing_user.get("email") == email:
                return error_response("邮箱已被注册")

        # 创建新用户
        new_user = {
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "role": role,
            "created_at": datetime.now().isoformat(),
            "is_active": True,
            "last_login": None
        }

        # 保存用户
        users[username] = new_user
        save_users(users)

        logger.info(f"新用户 {username} 注册成功")
        return success_response(
            data={"username": username, "email": email, "role": role},
            message="注册成功"
        )

    except Exception as e:
        logger.error(f"注册失败: {str(e)}")
        return error_response(f"注册失败: {str(e)}")

@router.get("/profile", response_model=APIResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    获取用户资料
    """
    try:
        user_profile = {
            "username": current_user["username"],
            "email": current_user["email"],
            "role": current_user["role"],
            "created_at": current_user["created_at"],
            "last_login": current_user.get("last_login")
        }

        return success_response(
            data=user_profile,
            message="获取用户资料成功"
        )

    except Exception as e:
        logger.error(f"获取用户资料失败: {str(e)}")
        return error_response(f"获取用户资料失败: {str(e)}")

@router.put("/profile", response_model=APIResponse)
async def update_profile(
    profile_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    更新用户资料
    """
    try:
        users = load_users()
        username = current_user["username"]

        # 可更新的字段
        updatable_fields = ["email"]
        updated_fields = []

        for field in updatable_fields:
            if field in profile_data:
                if field == "email":
                    new_email = profile_data[field].strip()
                    if "@" not in new_email or "." not in new_email:
                        return error_response("请输入有效的邮箱地址")

                    # 检查邮箱是否已被其他用户使用
                    for other_username, other_user in users.items():
                        if other_username != username and other_user.get("email") == new_email:
                            return error_response("邮箱已被其他用户使用")

                    users[username][field] = new_email
                    updated_fields.append(field)

        if updated_fields:
            save_users(users)
            logger.info(f"用户 {username} 更新了资料: {updated_fields}")

        return success_response(
            data={"updated_fields": updated_fields},
            message="资料更新成功"
        )

    except Exception as e:
        logger.error(f"更新用户资料失败: {str(e)}")
        return error_response(f"更新用户资料失败: {str(e)}")

@router.post("/change-password", response_model=APIResponse)
async def change_password(
    password_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    修改密码
    """
    try:
        current_password = password_data.get("currentPassword", "")
        new_password = password_data.get("newPassword", "")
        confirm_password = password_data.get("confirmPassword", "")

        if not current_password or not new_password or not confirm_password:
            return error_response("所有密码字段都不能为空")

        if new_password != confirm_password:
            return error_response("新密码确认不匹配")

        if len(new_password) < 8:
            return error_response("新密码长度至少8个字符")

        # 验证当前密码
        if not verify_password(current_password, current_user["password_hash"]):
            return error_response("当前密码错误")

        # 更新密码
        users = load_users()
        username = current_user["username"]
        users[username]["password_hash"] = hash_password(new_password)
        save_users(users)

        logger.info(f"用户 {username} 修改密码成功")
        return success_response(
            data={},
            message="密码修改成功"
        )

    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        return error_response(f"修改密码失败: {str(e)}")

@router.get("/users", response_model=APIResponse)
async def list_users(current_user: dict = Depends(get_current_user)):
    """
    获取用户列表（仅管理员）
    """
    try:
        if current_user.get("role") != "admin":
            return error_response("权限不足，仅管理员可以查看用户列表")

        users = load_users()
        user_list = []

        for username, user_data in users.items():
            user_list.append({
                "username": user_data["username"],
                "email": user_data["email"],
                "role": user_data["role"],
                "created_at": user_data["created_at"],
                "last_login": user_data.get("last_login"),
                "is_active": user_data.get("is_active", True)
            })

        # 按创建时间排序
        user_list.sort(key=lambda x: x["created_at"], reverse=True)

        return success_response(
            data=user_list,
            message=f"找到 {len(user_list)} 个用户"
        )

    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return error_response(f"获取用户列表失败: {str(e)}")

@router.put("/users/{username}/status", response_model=APIResponse)
async def update_user_status(
    username: str,
    status_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    更新用户状态（仅管理员）
    """
    try:
        if current_user.get("role") != "admin":
            return error_response("权限不足，仅管理员可以修改用户状态")

        if username == current_user["username"]:
            return error_response("不能修改自己的账户状态")

        users = load_users()
        if username not in users:
            return error_response("用户不存在")

        is_active = status_data.get("is_active")
        if is_active is not None:
            users[username]["is_active"] = bool(is_active)
            save_users(users)

            action = "启用" if is_active else "禁用"
            logger.info(f"管理员 {current_user['username']} {action}了用户 {username}")

            return success_response(
                data={"username": username, "is_active": is_active},
                message=f"用户账户已{action}"
            )
        else:
            return error_response("无效的状态数据")

    except Exception as e:
        logger.error(f"更新用户状态失败: {str(e)}")
        return error_response(f"更新用户状态失败: {str(e)}")

@router.delete("/users/{username}", response_model=APIResponse)
async def delete_user(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除用户（仅管理员）
    """
    try:
        if current_user.get("role") != "admin":
            return error_response("权限不足，仅管理员可以删除用户")

        if username == current_user["username"]:
            return error_response("不能删除自己的账户")

        users = load_users()
        if username not in users:
            return error_response("用户不存在")

        # 删除用户
        del users[username]
        save_users(users)

        logger.info(f"管理员 {current_user['username']} 删除了用户 {username}")
        return success_response(
            data={"username": username},
            message="用户已删除"
        )

    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        return error_response(f"删除用户失败: {str(e)}")

@router.post("/logout", response_model=APIResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    用户登出
    """
    try:
        # 在实际应用中，这里可以将token加入黑名单
        # 当前实现只是返回成功响应

        logger.info(f"用户 {current_user['username']} 登出")
        return success_response(
            data={},
            message="登出成功"
        )

    except Exception as e:
        logger.error(f"登出失败: {str(e)}")
        return error_response(f"登出失败: {str(e)}")

@router.get("/verify-token", response_model=APIResponse)
async def verify_user_token(current_user: dict = Depends(get_current_user)):
    """
    验证token有效性
    """
    try:
        return success_response(
            data={
                "username": current_user["username"],
                "role": current_user["role"],
                "valid": True
            },
            message="Token有效"
        )

    except Exception as e:
        logger.error(f"Token验证失败: {str(e)}")
        return error_response(f"Token验证失败: {str(e)}")

# 角色权限检查装饰器
def require_role(required_role: str):
    """
    要求特定角色的装饰器
    """
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "")

        # 角色层级：admin > operator > viewer
        role_hierarchy = {"admin": 3, "operator": 2, "viewer": 1}

        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 999)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 {required_role} 角色"
            )

        return current_user

    return role_checker

# 管理员权限检查
require_admin = require_role("admin")
# 操作员权限检查
require_operator = require_role("operator")