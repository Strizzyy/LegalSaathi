# Admin Cost Monitoring System - INTERNAL USE ONLY

## 🔒 Security Notice
This system is designed for **internal administrative use only** to monitor our Google Cloud API costs and usage. It should **never** be exposed to end users.

## 🏗️ Architecture Overview

### Backend Components

1. **Cost Monitoring Service** (`services/cost_monitoring_service.py`)
   - Real-time tracking of all Google Cloud AI service usage
   - Cost calculation with service-specific pricing models
   - SQLite database for usage storage and analytics
   - Email alert system for cost/quota thresholds

2. **Quota Manager** (`services/quota_manager.py`)
   - Multi-level rate limiting (per minute, hour, day)
   - Circuit breaker pattern for service reliability
   - Request batching and intelligent throttling
   - In-memory fallback when Redis unavailable

3. **Authentication Integration** (`controllers/auth_controller.py`)
   - Firebase token validation for admin access
   - Role-based authorization with admin email list
   - Secure endpoint protection

### Frontend Components

1. **Admin Dashboard** (`client/src/components/admin/AdminDashboard.tsx`)
   - Cost analytics with service breakdown
   - Real-time quota monitoring with visual indicators
   - System health status monitoring
   - Optimization suggestions display

2. **Admin Access Button** (`client/src/components/admin/AdminAccessButton.tsx`)
   - Automatically appears only for admin users
   - Integrated into main navigation
   - Secure access verification

3. **Admin Service** (`client/src/services/adminCostService.ts`)
   - TypeScript service for API communication
   - Automatic Firebase token handling
   - Type-safe interfaces

## 🔐 Security Implementation

### Backend Security
- All admin endpoints require Firebase authentication
- Admin access verified through environment-based email list
- Endpoints protected with `/api/admin/` prefix
- Comprehensive error handling and logging

### Frontend Security
- Admin components only render for authorized users
- Automatic access verification on component mount
- Secure token handling through Firebase Auth
- No cost data exposed to regular users

## 📊 Features

### Cost Analytics
- Daily and monthly cost tracking
- Service-wise cost breakdown with percentages
- Usage trend analysis
- Optimization suggestions based on patterns
- Potential cost savings calculations

### Quota Management
- Real-time usage monitoring across all time windows
- Visual progress bars with color-coded warnings
- Circuit breaker status monitoring
- Priority-based service management

### System Health
- Component-wise health status
- Database and cache connection monitoring
- Service availability tracking
- Automatic degradation detection

### Email Alerts
- Configurable cost and quota thresholds
- Automatic notifications to admin email
- HTML-formatted alert messages
- Integration with existing SMTP service

## 🚀 Usage

### For Administrators

1. **Access the Dashboard**
   - Log in with admin credentials
   - Admin button appears automatically in navigation
   - Click 🔒 Admin button to open dashboard

2. **Monitor Costs**
   - View daily/monthly costs in Analytics tab
   - Check service breakdown and trends
   - Review optimization suggestions

3. **Check Quotas**
   - Monitor usage percentages in Quotas tab
   - Watch for yellow (80%) and red (95%) warnings
   - Check circuit breaker status

4. **System Health**
   - Verify all components are healthy
   - Monitor database and cache connections
   - Check for any degraded services

### Configuration

#### Environment Variables
```env
# Admin access control
ADMIN_EMAILS=admin@company.com,manager@company.com
COST_ALERT_EMAIL=alerts@company.com

# Email notifications
GMAIL_SENDER_EMAIL=noreply@company.com
GMAIL_APP_PASSWORD=your_app_password
```

#### Cost Thresholds
- Warning threshold: 80% of quota
- Critical threshold: 95% of quota
- Daily cost alert: $50
- Monthly cost alert: $1000

## 🛠️ API Endpoints (Admin Only)

All endpoints require `Authorization: Bearer <firebase_token>` header:

- `GET /api/admin/costs/analytics?days=30` - Cost analytics
- `GET /api/admin/costs/quotas` - Quota status for all services
- `GET /api/admin/costs/health` - System health status
- `POST /api/admin/costs/optimize` - Request optimization

## 📈 Monitoring Services

The system tracks usage and costs for:
- **Vertex AI** (Primary) - Text generation, embeddings
- **Gemini API** (Fallback) - Text generation
- **Document AI** - Document processing
- **Natural Language AI** - Entity extraction, sentiment
- **Translation API** - Text translation
- **Vision API** - Image analysis
- **Speech API** - Speech-to-text

## 🔧 Technical Details

### Database Schema
- `api_usage` - Individual API call records
- `quota_tracking` - Service quota monitoring
- `cost_alerts` - Alert history and status

### Caching Strategy
- Redis for high-performance caching
- In-memory fallback for reliability
- TTL-based cache expiration
- Content-based cache keys

### Rate Limiting
- Token bucket algorithm
- Multiple time windows (minute/hour/day)
- Priority-based throttling
- Circuit breaker protection

## 🚨 Troubleshooting

### Common Issues

1. **Admin Access Denied**
   - Verify email is in `ADMIN_EMAILS` environment variable
   - Check Firebase authentication status
   - Ensure proper token format

2. **Cost Data Not Loading**
   - Check database connection in Health tab
   - Verify Google Cloud credentials
   - Review backend logs for errors

3. **Email Alerts Not Sending**
   - Verify SMTP configuration
   - Check `COST_ALERT_EMAIL` setting
   - Test email service connectivity

### Health Checks
- Database: SQLite connection and query execution
- Cache: Redis connection and operations
- Monitoring: Recent usage data availability

## 📝 Development Notes

### Adding New Services
1. Add service type to `ServiceType` enum
2. Configure pricing in `cost_config`
3. Set quota limits in `quota_limits`
4. Update frontend types if needed

### Modifying Thresholds
- Backend: Update `warning_threshold` and `critical_threshold`
- Frontend: Adjust `getUsageColor()` function
- Email: Modify alert templates

### Testing
- Use admin email for testing access
- Monitor logs for authentication issues
- Test with different quota scenarios

## 🔒 Security Best Practices

1. **Never expose cost data to end users**
2. **Keep admin email list minimal and secure**
3. **Regularly rotate Firebase tokens**
4. **Monitor admin access logs**
5. **Use HTTPS for all admin communications**
6. **Regularly review and update admin permissions**

---

**Remember: This system contains sensitive business information about our API costs and usage. Always maintain strict access controls and never expose this data publicly.**