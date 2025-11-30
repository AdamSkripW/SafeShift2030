"""
Quick database check - verify admin user and test data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.models import db, User, HospitalAdmin, Shift, BurnoutAlert, Hospital

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("  🏥 SAFESHIFT DATABASE CHECK")
    print("="*70)
    
    # 1. Check Hospitals
    print("\n1️⃣  HOSPITALS:")
    hospitals = Hospital.query.all()
    print(f"   Total: {len(hospitals)}")
    for h in hospitals:
        print(f"   - {h.Name} (ID: {h.HospitalId})")
    
    # 2. Check Users
    print("\n2️⃣  USERS:")
    users = User.query.all()
    print(f"   Total: {len(users)}")
    for u in users:
        print(f"   - {u.FirstName} {u.LastName} ({u.Role}) - {u.Email}")
        print(f"     Department: {u.Department}, Active: {u.IsActive}")
    
    # 3. Check Admin User
    print("\n3️⃣  ADMIN ACCOUNT CHECK:")
    admin_user = User.query.filter_by(Email='admin@hospital.sk').first()
    if admin_user:
        print(f"   ✅ Admin user exists!")
        print(f"      ID: {admin_user.UserId}")
        print(f"      Name: {admin_user.FirstName} {admin_user.LastName}")
        print(f"      Email: {admin_user.Email}")
        print(f"      Role: {admin_user.Role}")
        print(f"      Department: {admin_user.Department}")
        print(f"      Active: {admin_user.IsActive}")
        
        # Check if has HospitalAdmin entry
        admin_entry = HospitalAdmin.query.filter_by(UserId=admin_user.UserId).first()
        if admin_entry:
            print(f"   ✅ HospitalAdmin entry exists!")
            print(f"      Admin ID: {admin_entry.AdminId}")
            print(f"      Hospital ID: {admin_entry.HospitalId}")
            print(f"      Role: {admin_entry.Role}")
            print(f"      Permissions: ViewAll={admin_entry.PermissionsViewAll}, "
                  f"EditShifts={admin_entry.PermissionsEditShifts}, "
                  f"AssignTimeOff={admin_entry.PermissionsAssignTimeOff}")
        else:
            print(f"   ⚠️  No HospitalAdmin entry (admin can still login, but not in admins table)")
    else:
        print(f"   ❌ Admin user NOT FOUND!")
    
    # 4. Check Shifts
    print("\n4️⃣  SHIFTS:")
    shifts = Shift.query.all()
    print(f"   Total: {len(shifts)}")
    for s in shifts[:5]:  # Show first 5
        user = User.query.get(s.UserId)
        print(f"   - {user.FirstName if user else 'Unknown'}: {s.ShiftDate} "
              f"({s.ShiftType}, {s.ShiftLengthHours}h) - Index: {s.SafeShiftIndex} ({s.Zone})")
    if len(shifts) > 5:
        print(f"   ... and {len(shifts)-5} more")
    
    # 5. Check Burnout Alerts
    print("\n5️⃣  BURNOUT ALERTS:")
    alerts = BurnoutAlert.query.all()
    print(f"   Total: {len(alerts)}")
    for a in alerts:
        user = User.query.get(a.UserId)
        print(f"   - {user.FirstName if user else 'Unknown'}: {a.AlertType} "
              f"({a.Severity}) - Resolved: {a.IsResolved}")
    
    # 6. Summary for Admin Dashboard
    print("\n6️⃣  ADMIN DASHBOARD DATA AVAILABILITY:")
    
    # Count users by department
    icu_users = User.query.filter_by(Department='ICU').count()
    surgery_users = User.query.filter_by(Department='Surgery').count()
    
    print(f"   ICU Department: {icu_users} users")
    print(f"   Surgery Department: {surgery_users} users")
    
    # Count critical shifts
    critical_shifts = Shift.query.filter_by(Zone='red').count()
    warning_shifts = Shift.query.filter_by(Zone='yellow').count()
    safe_shifts = Shift.query.filter_by(Zone='green').count()
    
    print(f"   Red zone shifts: {critical_shifts}")
    print(f"   Yellow zone shifts: {warning_shifts}")
    print(f"   Green zone shifts: {safe_shifts}")
    
    # 7. Test admin can login
    print("\n7️⃣  ADMIN LOGIN TEST:")
    if admin_user:
        from werkzeug.security import check_password_hash
        test_password = "AdminPass123!"
        can_login = check_password_hash(admin_user.PasswordHash, test_password)
        if can_login:
            print(f"   ✅ Password verification SUCCESS!")
        else:
            print(f"   ❌ Password verification FAILED!")
            print(f"      (Password might be different or hash incorrect)")
    
    print("\n" + "="*70)
    print("  DATABASE CHECK COMPLETE")
    print("="*70 + "\n")
