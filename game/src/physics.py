"""Small swept steps shared by movement, forces and ground enemies."""
import math
import pygame

def move_axis(body, amount, platforms, axis):
    """Resolve the nearest surface, regardless of group order or thin walls."""
    remainder = getattr(body, '_motion_'+axis, 0.0) + amount
    pixels = math.trunc(remainder)
    setattr(body, '_motion_'+axis, remainder-pixels)
    blocked = False
    while pixels:
        step = max(-4, min(4, pixels))
        setattr(body.rect, axis, getattr(body.rect, axis)+step)
        hits = [p.rect for p in platforms if p is not body and body.rect.colliderect(p.rect)]
        if hits:
            if axis == 'x':
                if step > 0: body.rect.right = min(r.left for r in hits)
                else: body.rect.left = max(r.right for r in hits)
            else:
                if step > 0: body.rect.bottom = min(r.top for r in hits)
                else: body.rect.top = max(r.bottom for r in hits)
            setattr(body, '_motion_'+axis, 0.0)
            blocked = True
            break
        pixels -= step
    return blocked

def support(body, platforms, direction=1):
    probe = body.rect.move(0,direction)
    return next((p for p in platforms if p is not body and probe.colliderect(p.rect)),None)

def moving_platform_step(body, platform, dt, platforms):
    """Carry riders and push bystanders; reverse before trapping either in terrain."""
    old = platform.rect.copy()
    old_position = (platform.pos_x, platform.pos_y)
    before = body.rect.copy()
    remainders = (getattr(body, '_motion_x', 0), getattr(body, '_motion_y', 0))
    riding = (body.is_on_ground and body.velocity_y >= 0
              and abs(before.bottom-old.top) <= 2
              and before.right > old.left and before.left < old.right)
    platform.update_moving(dt)
    dx, dy = platform.rect.x-old.x, platform.rect.y-old.y
    solids = [p for p in platforms if p is not platform]
    blocked = False
    if riding:
        move_axis(body, dx, solids, 'x')
        blocked = move_axis(body, platform.rect.top-body.rect.bottom, solids, 'y')
        if not blocked:
            body.velocity_y = 0
    elif body.rect.colliderect(platform.rect):
        if platform.axis == 'horizontal' and dx:
            push = platform.rect.right-body.rect.left if dx > 0 else platform.rect.left-body.rect.right
            blocked = move_axis(body, push, solids, 'x')
        elif dy:
            push = platform.rect.bottom-body.rect.top if dy > 0 else platform.rect.top-body.rect.bottom
            blocked = move_axis(body, push, solids, 'y')
    if blocked or body.rect.colliderect(platform.rect):
        platform.rect = old
        platform.pos_x, platform.pos_y = old_position
        platform.direction *= -1
        body.rect = before
        body._motion_x, body._motion_y = remainders
    body.is_on_ground = support(body, platforms) is not None

def ground_move(body, vx, dt, platforms, avoid_edges=True):
    grounded = support(body,platforms) is not None
    direction = 1 if vx >= 0 else -1
    if grounded and avoid_edges and vx:
        probe=pygame.Rect(body.rect.centerx+direction*(body.rect.width//2+12),body.rect.bottom,2,12)
        if not any(probe.colliderect(p.rect) for p in platforms):
            vx=0
            if hasattr(body,'direction'): body.direction=-direction
    wall=move_axis(body,vx*dt,platforms,'x')
    if wall and hasattr(body,'direction'): body.direction=-direction
    body.velocity_y=min(720,getattr(body,'velocity_y',0)+1800*dt)
    landed=move_axis(body,body.velocity_y*dt,platforms,'y')
    if landed: body.velocity_y=0
    body.on_ground=support(body,platforms) is not None
    if hasattr(body,'pos_x'): body.pos_x=float(body.rect.x)
    return wall

def top_contact(previous, current, target, descending):
    return descending and previous.bottom <= target.top+8 and current.bottom >= target.top and current.right>target.left+3 and current.left<target.right-3

def projectile_hits(projectile,target):
    previous=getattr(projectile,'previous_rect',projectile.rect)
    # Segment against an expanded target is a swept AABB test, not a broad union.
    expanded=target.inflate(projectile.rect.w,projectile.rect.h)
    return projectile.rect.colliderect(target) or bool(expanded.clipline(previous.center,projectile.rect.center))
