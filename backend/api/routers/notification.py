from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from uuid import UUID
from api.models import Notification, User
from api.schemas import NotificationSchema, NotificationListResponseSchema, NotificationDetailResponseSchema

router = Router()


@router.get('/', response=NotificationListResponseSchema)
def list_notifications(request, limit: int = 25, offset: int = 0, includeSeen: bool = True):
    """List notifications for the authenticated user"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    query = Notification.objects.filter(user=user)
    
    # If includeSeen is False, only show unread notifications
    if not includeSeen:
        query = query.filter(read=False)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    notifications = query.order_by('-created_at')[offset:offset + limit]
    
    return {
        'notifications': notifications,
        'limit': limit,
        'offset': offset,
        'total': total
    }


@router.get('/unseen')
def get_unseen_count(request):
    """Get count of unseen notifications for the authenticated user"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    count = Notification.objects.filter(user=user, read=False).count()
    
    return {'unseen': count}


@router.patch('/read-all')
def mark_all_notifications_read(request):
    """Mark all notifications as read for the authenticated user"""
    user_uid = request.auth.get('user', {}).get('uid')
    user = get_object_or_404(User, uid=user_uid)
    
    # Update all unread notifications for this user
    count = Notification.objects.filter(user=user, read=False).update(read=True)
    
    return {'success': True, 'count': count}


@router.get('/{notification_uid}', response=NotificationDetailResponseSchema)
def get_notification(request, notification_uid: UUID):
    """Get a single notification"""
    user_uid = request.auth.get('user', {}).get('uid')
    notification = get_object_or_404(Notification, uid=notification_uid, user__uid=user_uid)
    
    return {
        'notification': notification
    }


@router.patch('/{notification_uid}/read')
def mark_notification_read(request, notification_uid: UUID):
    """Mark a notification as read"""
    user_uid = request.auth.get('user', {}).get('uid')
    notification = get_object_or_404(Notification, uid=notification_uid, user__uid=user_uid)
    
    notification.read = True
    notification.save()
    
    return {'success': True}


@router.delete('/{notification_uid}')
def delete_notification(request, notification_uid: UUID):
    """Delete a notification"""
    user_uid = request.auth.get('user', {}).get('uid')
    notification = get_object_or_404(Notification, uid=notification_uid, user__uid=user_uid)
    
    notification.delete()
    
    return {'success': True}
