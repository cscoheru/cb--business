# Admin Dashboard Design Document

**Project**: CB-Business (ZenConsult)
**Date**: 2026-03-13
**Version**: 1.0
**Author**: Architecture Team

---

## Executive Summary

This document outlines the design and implementation plan for an administrative dashboard to manage the CB-Business SaaS platform. The admin dashboard will provide administrators with tools to manage users, subscriptions, content (cards and articles), view analytics, and monitor system health.

**Recommended Approach**: Extend the existing Next.js frontend with an `/admin` route group, leveraging the existing shadcn/ui component library for consistency.

**Estimated Implementation Time**: 3-4 weeks

---

## 1. Architecture Decision

### 1.1 Recommended Approach: Extended Frontend with Route Group

**Decision**: Build the admin dashboard as a route group (`/app/admin/...`) within the existing Next.js frontend project.

#### Rationale

| Factor | Extended Frontend | Separate Admin Project |
|--------|------------------|----------------------|
| **Development Speed** | Fast (reuse components, auth, API) | Slow (new setup, duplication) |
| **Code Maintainability** | High (single codebase) | Medium (separate codebases) |
| **UI Consistency** | Native (same components) | Manual sync required |
| **Deployment** | Simple (one Vercel project) | Complex (multiple deployments) |
| **Security** | Route-level protection | Separate auth system |
| **Performance** | Good (code splitting) | Better (smaller bundles) |

#### Security Advantages

- **Shared Authentication**: Leverages existing JWT-based auth system
- **Route Protection**: Middleware-based admin verification at `/admin` level
- **Token-based**: Uses existing `user.is_admin` flag in JWT payload
- **Single Source of Truth**: No auth system duplication

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Vercel Deployment                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Next.js App Router                     │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │                                                     │    │
│  │  ┌──────────────────┐      ┌──────────────────┐    │    │
│  │  │  User Routes     │      │  Admin Routes    │    │    │
│  │  │  /app/           │      │  /app/admin/     │    │    │
│  │  │  ├── /login      │      │  ├── /dashboard  │    │    │
│  │  │  ├── /register   │      │  ├── /users      │    │    │
│  │  │  ├── /cards      │      │  ├── /subs       │    │    │
│  │  │  └── /dashboard  │      │  ├── /content    │    │    │
│  │  │                  │      │  ├── /analytics  │    │    │
│  │  │                  │      │  └── /settings   │    │    │
│  │  └──────────────────┘      └──────────────────┘    │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │           Middleware (Admin Gate)            │  │    │
│  │  │  • Verify user.is_admin flag                │  │    │
│  │  │  • Redirect non-admins to /403              │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                    │
│                          ▼                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              FastAPI Backend                         │    │
│  │  • /api/v1/admin/* endpoints                        │    │
│  │  • get_admin_user dependency                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                    │
│                          ▼                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              PostgreSQL Database                     │    │
│  │  • users (is_admin flag)                            │    │
│  │  • subscriptions                                    │    │
│  │  • cards, articles                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Admin Role & Permission Design

### 2.1 Current User Model

The existing `User` model already includes an `is_admin` boolean flag:

```python
# backend/models/user.py
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    # ... other fields ...
    is_admin = Column(Boolean, default=False, nullable=False)
```

### 2.2 Permission Model (Future Extension)

For Phase 2, consider extending to a role-based permission system:

```python
# Future: models/role.py
class AdminRole(Base):
    __tablename__ = "admin_roles"

    id = Column(UUID, primary_key=True)
    name = Column(String(50), unique=True)  # super_admin, content_manager, support
    permissions = Column(JSONB)  # List of permission strings

class AdminPermission(Enum):
    # User Management
    VIEW_USERS = "view_users"
    EDIT_USERS = "edit_users"
    BAN_USERS = "ban_users"
    DELETE_USERS = "delete_users"

    # Subscription Management
    VIEW_SUBSCRIPTIONS = "view_subscriptions"
    MODIFY_SUBSCRIPTIONS = "modify_subscriptions"
    CANCEL_SUBSCRIPTIONS = "cancel_subscriptions"
    REFUND_PAYMENTS = "refund_payments"

    # Content Management
    VIEW_CONTENT = "view_content"
    EDIT_CARDS = "edit_cards"
    EDIT_ARTICLES = "edit_articles"
    PUBLISH_CONTENT = "publish_content"
    DELETE_CONTENT = "delete_content"

    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"

    # System
    MANAGE_ADMINS = "manage_admins"
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SETTINGS = "manage_settings"
```

### 2.3 Admin Access Verification

Existing backend dependency (`/backend/api/dependencies.py`):

```python
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify current user is admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_ADMIN", "message": "Admin access required"}
        )
    return current_user
```

---

## 3. Feature Requirements & Priority

### 3.1 Phase 1: Core Admin Features (Week 1-2)

| Priority | Feature | Description | User Story |
|----------|---------|-------------|------------|
| **P0** | Admin Dashboard Home | Overview with key metrics | As admin, I want to see platform stats at a glance |
| **P0** | User Management | List, view, edit, ban users | As admin, I need to manage user accounts |
| **P0** | Subscription Management | View, modify, cancel subscriptions | As admin, I need to handle subscription issues |
| **P1** | Content Management - Cards | View, edit, publish/unpublish cards | As admin, I want to curate card content |
| **P1** | Content Management - Articles | View, edit, publish/unpublish articles | As admin, I want to manage article content |

### 3.2 Phase 2: Analytics & Insights (Week 3)

| Priority | Feature | Description | User Story |
|----------|---------|-------------|------------|
| **P1** | User Analytics | User growth, retention, active users | As admin, I want to track user engagement |
| **P1** | Revenue Analytics | MRR, subscriptions, payment trends | As admin, I need to monitor revenue |
| **P2** | Content Analytics | Card/article views, engagement | As admin, I want to know what content performs |
| **P2** | Export Data | CSV/Excel export functionality | As admin, I want to export data for analysis |

### 3.3 Phase 3: Advanced Features (Week 4)

| Priority | Feature | Description | User Story |
|----------|---------|-------------|------------|
| **P2** | System Health | API status, database, Redis, crawler | As admin, I want to monitor system health |
| **P2** | Activity Logs | Admin action audit trail | As admin, I want to track admin actions |
| **P3** | User Impersonation | Login as any user for support | As admin, I want to troubleshoot user issues |
| **P3** | Bulk Operations | Bulk ban, bulk publish, etc. | As admin, I want to perform bulk actions |

---

## 4. Tech Stack

### 4.1 Frontend

| Category | Technology | Rationale |
|----------|-----------|-----------|
| **Framework** | Next.js 16 (App Router) | Existing framework, SSR/SSG support |
| **UI Library** | shadcn/ui | Already integrated, consistent design |
| **Styling** | Tailwind CSS 4 | Existing setup |
| **Charts** | Recharts 3.8 | Already installed, lightweight |
| **Tables** | TanStack Table (React Table v8) | Powerful headless table for admin data |
| **Forms** | React Hook Form + Zod | Existing validation stack |
| **State Management** | React Context / Server Components | Minimal client state needed |
| **Date Handling** | date-fns | Lightweight, tree-shakeable |

### 4.2 Backend

| Category | Technology | Rationale |
|----------|-----------|-----------|
| **Framework** | FastAPI | Existing backend |
| **Database** | PostgreSQL (AsyncPG) | Existing database |
| **ORM** | SQLAlchemy 2.0 (Async) | Existing ORM |
| **Admin Router** | `/api/v1/admin/*` | Namespace for admin endpoints |

### 4.3 New Dependencies to Add

```json
{
  "dependencies": {
    "@tanstack/react-table": "^8.20.1",
    "date-fns": "^3.6.0"
  }
}
```

---

## 5. Frontend Implementation Plan

### 5.1 Directory Structure

```
frontend/
├── app/
│   ├── (user)/                    # Existing user routes
│   │   ├── login/
│   │   ├── cards/
│   │   └── dashboard/
│   │
│   └── admin/                     # NEW: Admin route group
│       ├── layout.tsx             # Admin layout with sidebar
│       ├── middleware.ts          # Admin access verification
│       ├── page.tsx               # Admin dashboard home
│       ├── users/
│       │   ├── page.tsx           # User list
│       │   └── [id]/
│       │       └── page.tsx       # User detail
│       ├── subscriptions/
│       │   ├── page.tsx           # Subscription list
│       │   └── [id]/
│       │       └── page.tsx       # Subscription detail
│       ├── content/
│       │   ├── page.tsx           # Content overview
│       │   ├── cards/
│       │   │   ├── page.tsx       # Card management
│       │   │   └── [id]/
│       │   │       └── page.tsx   # Card detail/edit
│       │   └── articles/
│       │       ├── page.tsx       # Article management
│       │       └── [id]/
│       │           └── page.tsx   # Article detail/edit
│       ├── analytics/
│       │   ├── page.tsx           # Analytics overview
│       │   ├── users/
│       │   │   └── page.tsx       # User analytics
│       │   └── revenue/
│       │       └── page.tsx       # Revenue analytics
│       └── settings/
│           └── page.tsx           # Admin settings
│
├── components/
│   └── admin/                     # NEW: Admin-specific components
│       ├── AdminSidebar.tsx       # Navigation sidebar
│       ├── AdminHeader.tsx        # Top bar with user menu
│       ├── DataTable.tsx          # Reusable data table
│       ├── StatCard.tsx           # Metric card
│       ├── UserActions.tsx        # User action buttons
│       ├── SubscriptionActions.tsx
│       └── ContentActions.tsx
│
├── lib/
│   └── admin-api.ts               # NEW: Admin API client
│
└── types/
    └── admin.ts                   # NEW: Admin TypeScript types
```

### 5.2 Admin Middleware

**File**: `/frontend/app/admin/middleware.ts`

```typescript
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { getToken } from '@/lib/api'

export async function adminMiddleware(request: NextRequest) {
  const token = getToken()
  const path = request.nextUrl.pathname

  // Only protect admin routes
  if (!path.startsWith('/admin')) {
    return NextResponse.next()
  }

  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Verify admin status by checking user API
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/me`, {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (!response.ok) {
      return NextResponse.redirect(new URL('/login', request.url))
    }

    const user = await response.json()

    if (!user.is_admin) {
      return NextResponse.redirect(new URL('/403', request.url))
    }

    return NextResponse.next()
  } catch (error) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
}
```

### 5.3 Admin Layout

**File**: `/frontend/app/admin/layout.tsx`

```typescript
import { AdminSidebar } from '@/components/admin/AdminSidebar'
import { AdminHeader } from '@/components/admin/AdminHeader'

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <AdminSidebar />
      <div className="lg:pl-64">
        <AdminHeader />
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
```

---

## 6. Backend API Design

### 6.1 Existing Admin Endpoints

The following admin endpoints already exist in `/backend/api/admin.py`:

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/api/v1/admin/users` | POST | Get user list | ✅ Existing |
| `/api/v1/admin/users/stats` | GET | User statistics | ✅ Existing |
| `/api/v1/admin/subscriptions` | POST | Get subscription list | ✅ Existing |
| `/api/v1/admin/finance` | GET | Financial data | ✅ Existing |
| `/api/v1/admin/analytics` | GET | Analytics data | ✅ Existing |

### 6.2 New Admin Endpoints Required

#### User Management

```python
# backend/api/admin.py (additions)

@router.get("/admin/users/{user_id}")
async def get_user_detail(
    user_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user information"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/admin/users/{user_id}")
async def update_user(
    user_id: UUID,
    updates: UserUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user information"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in updates.dict(exclude_unset=True).items():
        setattr(user, field, value)

    await db.commit()
    return user

@router.post("/admin/users/{user_id}/ban")
async def ban_user(
    user_id: UUID,
    reason: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Ban a user"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.plan_status = PlanStatus.CANCELED
    # Add ban reason to a separate table
    await db.commit()
    return {"success": True}

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a user"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.deleted_at = datetime.utcnow()
    await db.commit()
    return {"success": True}
```

#### Content Management

```python
# backend/api/admin/content.py (new file)

router = APIRouter(prefix="/api/v1/admin/content", tags=["admin-content"])

@router.get("/cards")
async def get_admin_cards(
    status: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get cards for admin management"""
    query = select(Card)

    if status == "published":
        query = query.where(Card.is_published == True)
    elif status == "draft":
        query = query.where(Card.is_published == False)

    if category:
        query = query.where(Card.category == category)

    # Pagination
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    cards = result.scalars().all()

    return {"cards": cards, "total": len(cards)}

@router.put("/cards/{card_id}/publish")
async def publish_card(
    card_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Publish a card"""
    card = await db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.is_published = True
    card.published_at = datetime.utcnow()
    await db.commit()
    return {"success": True}

@router.delete("/cards/{card_id}")
async def delete_card(
    card_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a card"""
    card = await db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    await db.delete(card)
    await db.commit()
    return {"success": True}

@router.get("/articles")
async def get_admin_articles(
    status: Optional[str] = None,
    source: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get articles for admin management"""
    # Similar implementation to cards
    pass

@router.put("/articles/{article_id}/publish")
async def publish_article(
    article_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Publish an article"""
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.is_published = True
    await db.commit()
    return {"success": True}
```

#### Subscription Management

```python
# backend/api/admin/subscriptions.py (additions)

@router.get("/admin/subscriptions/{subscription_id}")
async def get_subscription_detail(
    subscription_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed subscription information"""
    sub = await db.get(Subscription, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub

@router.put("/admin/subscriptions/{subscription_id}")
async def modify_subscription(
    subscription_id: UUID,
    updates: SubscriptionUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Modify subscription (plan, expiration, etc.)"""
    sub = await db.get(Subscription, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    for field, value in updates.dict(exclude_unset=True).items():
        setattr(sub, field, value)

    await db.commit()
    return sub

@router.post("/admin/subscriptions/{subscription_id}/cancel")
async def admin_cancel_subscription(
    subscription_id: UUID,
    reason: str,
    refund: bool = False,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a subscription (admin override)"""
    sub = await db.get(Subscription, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    sub.status = "canceled"
    sub.canceled_at = datetime.utcnow()
    sub.auto_renew = False

    # Handle refund if requested
    if refund:
        # Integrate with payment provider for refund
        pass

    await db.commit()
    return {"success": True}
```

---

## 7. Admin UI Components

### 7.1 Component Specifications

#### AdminSidebar

```typescript
// components/admin/AdminSidebar.tsx
const navigation = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { name: 'Users', href: '/admin/users', icon: Users },
  { name: 'Subscriptions', href: '/admin/subscriptions', icon: CreditCard },
  { name: 'Content', href: '/admin/content', icon: FileText },
  { name: 'Analytics', href: '/admin/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/admin/settings', icon: Settings },
]
```

#### DataTable (Reusable)

Features:
- Server-side pagination
- Sorting
- Filtering
- Row selection
- Bulk actions
- Loading states

#### StatCard

```typescript
interface StatCardProps {
  title: string
  value: string | number
  change?: number
  icon: React.ReactNode
  period?: string
}
```

### 7.2 Page Templates

#### User List Page

```typescript
// app/admin/users/page.tsx
'use client'

import { DataTable } from '@/components/admin/DataTable'
import { UserActions } from '@/components/admin/UserActions'

const columns = [
  { key: 'email', label: 'Email', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'subscription', label: 'Plan', filterable: true },
  { key: 'status', label: 'Status', filterable: true },
  { key: 'createdAt', label: 'Joined', sortable: true },
  { key: 'actions', label: 'Actions', render: (row) => <UserActions user={row} /> }
]

export default function AdminUsersPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold">User Management</h1>
      <DataTable
        columns={columns}
        fetchData="/api/v1/admin/users"
        filters={['status', 'plan_tier', 'search']}
      />
    </div>
  )
}
```

---

## 8. Security Considerations

### 8.1 Authentication & Authorization

1. **JWT Verification**: All admin routes verify the JWT token
2. **Admin Flag Check**: Every admin endpoint checks `user.is_admin`
3. **Middleware Protection**: Server middleware at `/admin` route level
4. **Token Refresh**: Automatic token refresh for long admin sessions

### 8.2 Data Protection

1. **Sensitive Data Masking**: Partial email/phone display in lists
2. **Audit Logging**: Log all admin actions (create, update, delete)
3. **Soft Deletes**: Never hard delete user data
4. **Rate Limiting**: Stricter limits on admin endpoints

### 8.3 Audit Log Model (Future)

```python
# models/audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True)
    admin_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String(50))  # create, update, delete, ban, etc.
    resource_type = Column(String(50))  # user, subscription, card, article
    resource_id = Column(UUID)
    changes = Column(JSONB)  # Before/after values
    ip_address = Column(String(45))
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 8.4 Best Practices

- **Never expose admin endpoints in API documentation**
- **Use different token expiration for admin sessions**
- **Implement IP whitelisting for production admin access**
- **Regular security audits of admin permissions**
- **Two-factor authentication for admin accounts (Phase 2)**

---

## 9. Implementation Phases

### Phase 1: Foundation & User Management (Week 1)

**Backend Tasks:**
- [ ] Add user detail, update, ban endpoints
- [ ] Add soft delete functionality
- [ ] Create admin action logging system
- [ ] Write unit tests for admin endpoints

**Frontend Tasks:**
- [ ] Set up `/app/admin` route structure
- [ ] Create admin layout with sidebar
- [ ] Implement admin middleware
- [ ] Build user list page with DataTable
- [ ] Build user detail/edit pages
- [ ] Add ban/unban functionality

**Estimated Time**: 5-7 days

### Phase 2: Subscription Management (Week 2)

**Backend Tasks:**
- [ ] Add subscription detail endpoint
- [ ] Add subscription modification endpoint
- [ ] Add admin cancel subscription endpoint
- [ ] Integrate with payment provider for refunds

**Frontend Tasks:**
- [ ] Build subscription list page
- [ ] Build subscription detail page
- [ ] Add subscription modification UI
- [ ] Add cancel/refund confirmation flow

**Estimated Time**: 5-7 days

### Phase 3: Content Management (Week 3)

**Backend Tasks:**
- [ ] Create `/api/v1/admin/content/*` endpoints
- [ ] Add publish/unpublish endpoints
- [ ] Add bulk operations
- [ ] Add content analytics endpoints

**Frontend Tasks:**
- [ ] Build content overview dashboard
- [ ] Build card management page
- [ ] Build article management page
- [ ] Add content editor integration
- [ ] Implement bulk publish/unpublish

**Estimated Time**: 5-7 days

### Phase 4: Analytics & System Monitoring (Week 4)

**Backend Tasks:**
- [ ] Enhance analytics endpoints
- [ ] Add export functionality
- [ ] Add system health endpoints
- [ ] Integrate with crawler status

**Frontend Tasks:**
- [ ] Build analytics dashboard
- [ ] Add charts for user growth
- [ ] Add revenue visualization
- [ ] Add content performance charts
- [ ] Build system health page
- [ ] Add CSV/Excel export

**Estimated Time**: 5-7 days

---

## 10. Testing Strategy

### 10.1 Backend Testing

```python
# tests/test_admin.py
pytest tests/test_admin.py -v

# Test cases:
- test_admin_access_without_admin_flag_returns_403
- test_admin_users_list_returns_paginated_data
- test_admin_ban_user_sets_canceled_status
- test_admin_publish_card_sets_published_flag
- test_admin_cancel_subscription_updates_status
- test_non_admin_cannot_access_admin_routes
```

### 10.2 Frontend Testing

```typescript
// e2e/admin.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin user
    await page.goto('/login')
    await page.fill('[name="email"]', 'admin@zenconsult.top')
    await page.fill('[name="password"]', 'admin-password')
    await page.click('button[type="submit"]')
  })

  test('should display admin dashboard', async ({ page }) => {
    await page.goto('/admin')
    await expect(page.locator('h1')).toContainText('Admin Dashboard')
  })

  test('should display user list', async ({ page }) => {
    await page.goto('/admin/users')
    await expect(page.locator('table')).toBeVisible()
  })

  test('non-admin should be redirected', async ({ page, context }) => {
    // Clear admin session, login as regular user
    await context.clearCookies()
    await page.goto('/login')
    await page.fill('[name="email"]', 'user@example.com')
    await page.fill('[name="password"]', 'user-password')
    await page.click('button[type="submit"]')

    await page.goto('/admin')
    await expect(page).toHaveURL('/403')
  })
})
```

---

## 11. Deployment Plan

### 11.1 Deployment Checklist

- [ ] Review all admin endpoints for security vulnerabilities
- [ ] Set up admin user accounts in production database
- [ ] Configure environment variables for admin features
- [ ] Set up monitoring for admin actions
- [ ] Create admin access documentation
- [ ] Train administrators on dashboard usage
- [ ] Set up backup admin accounts
- [ ] Configure IP whitelisting (if applicable)

### 11.2 Rollout Strategy

1. **Staging Deployment**: Deploy to staging environment first
2. **Admin Testing**: Test all admin functions with staging data
3. **Production Deployment**: Deploy to production during low-traffic hours
4. **Verification**: Verify admin access with production admin accounts
5. **Monitoring**: Monitor admin logs for first week

### 11.3 Environment Variables

```env
# .env.production
NEXT_PUBLIC_API_URL=https://api.zenconsult.top
ADMIN_SESSION_TIMEOUT=28800  # 8 hours
ADMIN_RATE_LIMIT=100  # requests per hour
ADMIN_AUDIT_LOG_ENABLED=true
```

---

## 12. Maintenance & Operations

### 12.1 Monitoring Metrics

- Admin login count
- Admin actions performed (by type)
- Failed admin access attempts
- API response times for admin endpoints
- Admin session duration

### 12.2 Regular Tasks

- Review audit logs weekly
- Update admin permissions as needed
- Monitor for suspicious admin activity
- Backup admin-related data
- Review and update admin documentation

### 12.3 Escalation Procedures

1. **Admin Account Compromise**: Immediate password reset, revoke sessions
2. **Unauthorized Admin Access**: Lock admin routes, investigate logs
3. **Data Breach**: Trigger incident response, notify users

---

## 13. Future Enhancements (Phase 2+)

### 13.1 Advanced Features

- **Role-Based Access Control (RBAC)**: Multiple admin roles with different permissions
- **Two-Factor Authentication (2FA)**: Enhanced security for admin accounts
- **User Impersonation**: Support tool for troubleshooting user issues
- **Advanced Analytics**: Cohort analysis, funnel analysis
- **A/B Testing Dashboard**: Manage feature flags and experiments
- **Admin API Documentation**: Internal docs for admin endpoints
- **Bulk Import/Export**: CSV import for users, content
- **Email Campaign Management**: Send emails to user segments

### 13.2 Integrations

- **Payment Provider Dashboard**: Direct Stripe/Alipay integration
- **Customer Support**: Intercom/Zendesk integration
- **Error Tracking**: Sentry integration for admin errors
- **Analytics**: Google Analytics/Amplitude integration

---

## 14. Appendix

### 14.1 Admin User Setup

To create the first admin user:

```sql
-- Direct database query
UPDATE users
SET is_admin = true
WHERE email = 'admin@zenconsult.top';

-- Or via Python script
python scripts/create_admin.py --email admin@zenconsult.top
```

### 14.2 API Endpoint Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/users` | POST | List users with filters |
| `/api/v1/admin/users/stats` | GET | User statistics |
| `/api/v1/admin/users/{id}` | GET | User details |
| `/api/v1/admin/users/{id}` | PUT | Update user |
| `/api/v1/admin/users/{id}/ban` | POST | Ban user |
| `/api/v1/admin/subscriptions` | POST | List subscriptions |
| `/api/v1/admin/subscriptions/{id}` | GET | Subscription details |
| `/api/v1/admin/subscriptions/{id}` | PUT | Modify subscription |
| `/api/v1/admin/content/cards` | GET | List cards |
| `/api/v1/admin/content/cards/{id}/publish` | PUT | Publish card |
| `/api/v1/admin/content/articles` | GET | List articles |
| `/api/v1/admin/finance` | GET | Financial data |
| `/api/v1/admin/analytics` | GET | Analytics data |

### 14.3 References

- [Next.js App Router Documentation](https://nextjs.org/docs/app)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [TanStack Table Documentation](https://tanstack.com/table/v8)

---

**Document Status**: Ready for Review
**Next Steps**: Schedule architecture review meeting with development team
