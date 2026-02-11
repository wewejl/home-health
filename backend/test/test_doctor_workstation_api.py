"""
Doctor Workstation API tests for the home health backend.

Tests cover:
- Doctor information retrieval
- Patient statistics
- Patient list and search
- Patient assignment/unassignment
- Patient details and consultations
- Medical order creation and management
- Task tracking for patients

Uses test mode tokens (test_1) for authentication.
"""
import pytest
import os
from datetime import date, datetime

# Set test mode before imports
os.environ["TEST_MODE"] = "true"


def get_test_doctor(db_session):
    """
    Helper function to get or create the test_doctor.
    In test mode, the test_doctor is created lazily when the API is first called.
    """
    from app.models.admin_user import AdminUser

    test_doctor = db_session.query(AdminUser).filter(
        AdminUser.username == "test_doctor"
    ).first()

    # If test_doctor doesn't exist yet, create it manually
    if not test_doctor:
        from app.services.admin_auth_service import AdminAuthService
        test_doctor = AdminUser(
            username="test_doctor",
            email="doctor@example.com",
            role="doctor",
            is_active=True
        )
        test_doctor.password_hash = AdminAuthService.hash_password("test123")
        db_session.add(test_doctor)
        db_session.flush()

    return test_doctor


class TestGetDoctorInfo:
    """Tests for retrieving doctor information."""

    def test_get_doctor_info_success(self, test_client):
        """Test getting doctor info successfully."""
        response = test_client.get("/api/doctor/me", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "managed_doctors" in data
        assert isinstance(data["managed_doctors"], list)

    def test_get_doctor_info_without_auth(self, test_client):
        """Test getting doctor info without auth header."""
        # In test mode, auto-creates test doctor
        response = test_client.get("/api/doctor/me")
        assert response.status_code == 200


class TestGetPatientStats:
    """Tests for retrieving patient statistics."""

    def test_get_patient_stats_success(self, test_client):
        """Test getting patient stats successfully."""
        response = test_client.get("/api/doctor/patient-stats", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "active" in data
        assert "new_today" in data
        assert "low_compliance" in data
        # Stats should be non-negative integers
        assert data["total"] >= 0
        assert data["active"] >= 0
        assert data["new_today"] >= 0
        assert data["low_compliance"] >= 0

    def test_get_patient_stats_empty(self, test_client):
        """Test patient stats when doctor has no patients."""
        response = test_client.get("/api/doctor/patient-stats", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        # Should return zeros when no patients
        assert data["total"] == 0
        assert data["active"] == 0


class TestGetPatients:
    """Tests for retrieving patient list."""

    def test_get_patients_success(self, test_client):
        """Test getting patient list successfully."""
        response = test_client.get("/api/doctor/patients", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_patients_with_search(self, test_client, db_session):
        """Test searching patients by name or phone."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13800138999",
            nickname="搜索测试患者",
            gender="male",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with the test_doctor (authenticated user)
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.commit()

        # Search by nickname
        response = test_client.get("/api/doctor/patients?search=搜索测试", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_patients_empty(self, test_client):
        """Test getting patients when none assigned."""
        response = test_client.get("/api/doctor/patients", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # May be empty or contain department-related patients


class TestAssignPatient:
    """Tests for assigning patients to doctors."""

    def test_assign_patient_success(self, test_client, db_session):
        """Test assigning a patient successfully."""
        from app.models.user import User

        # Create test patient
        patient = User(
            phone="13900139888",
            nickname="待分配患者",
            gender="female",
            is_active=True
        )
        db_session.add(patient)
        db_session.commit()

        # Assign patient (test mode uses test_doctor)
        response = test_client.post("/api/doctor/patients/assign",
            headers={"Authorization": "Bearer test_1"},
            json={
                "patient_id": patient.id,
                "relationship_type": "primary",
                "notes": "测试分配"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == patient.id
        assert data["relationship_type"] == "primary"
        assert data["notes"] == "测试分配"
        assert data["is_active"] is True

    def test_assign_patient_not_exists(self, test_client):
        """Test assigning non-existent patient."""
        response = test_client.post("/api/doctor/patients/assign",
            headers={"Authorization": "Bearer test_1"},
            json={
                "patient_id": 99999,
                "relationship_type": "primary"
            }
        )
        assert response.status_code == 404

    def test_assign_patient_invalid_type(self, test_client):
        """Test assigning patient with invalid relationship type."""
        response = test_client.post("/api/doctor/patients/assign",
            headers={"Authorization": "Bearer test_1"},
            json={
                "patient_id": 1,
                "relationship_type": "invalid_type"
            }
        )
        # Should fail validation
        assert response.status_code == 422


class TestGetAssignablePatients:
    """Tests for getting list of assignable patients."""

    def test_get_assignable_patients_success(self, test_client):
        """Test getting assignable patients successfully."""
        response = test_client.get("/api/doctor/patients/assignable", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Each patient should have is_assigned field
        for patient in data:
            assert "is_assigned" in patient
            assert "id" in patient
            assert "nickname" in patient or "phone" in patient

    def test_get_assignable_patients_with_search(self, test_client):
        """Test searching assignable patients."""
        response = test_client.get("/api/doctor/patients/assignable?search=138", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_assignable_patients_with_limit(self, test_client):
        """Test assignable patients with limit."""
        response = test_client.get("/api/doctor/patients/assignable?limit=5", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5


class TestUnassignPatient:
    """Tests for unassigning patients from doctors."""

    def test_unassign_patient_success(self, test_client, db_session):
        """Test unassigning a patient successfully."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13900139777",
            nickname="待解除患者",
            gender="male",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with test_doctor
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.commit()

        # Unassign patient
        response = test_client.delete(f"/api/doctor/patients/{patient.id}/unassign", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_unassign_patient_not_found(self, test_client):
        """Test unassigning patient with no active relationship."""
        response = test_client.delete("/api/doctor/patients/99999/unassign", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 404


class TestGetPatientDetail:
    """Tests for retrieving patient details."""

    def test_get_patient_detail_with_access(self, test_client, db_session):
        """Test getting patient detail when doctor has access."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13900139666",
            nickname="详情测试患者",
            gender="female",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with test_doctor
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.commit()

        # Get patient detail
        response = test_client.get(f"/api/doctor/patients/{patient.id}", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == patient.id
        assert "nickname" in data
        assert "phone" in data
        assert "active_orders_count" in data
        assert "completion_rate" in data

    def test_get_patient_detail_no_access(self, test_client, db_session):
        """Test getting patient detail when doctor has no access."""
        from app.models.user import User

        # Create a patient with no relationship
        patient = User(
            phone="13900139555",
            nickname="无权限患者",
            gender="male",
            is_active=True
        )
        db_session.add(patient)
        db_session.commit()

        # Try to get patient detail without access
        response = test_client.get(f"/api/doctor/patients/{patient.id}", headers={
            "Authorization": "Bearer test_1"
        })
        # Should get 403 Forbidden
        assert response.status_code == 403

    def test_get_patient_detail_not_exists(self, test_client):
        """Test getting non-existent patient detail."""
        response = test_client.get("/api/doctor/patients/99999", headers={
            "Authorization": "Bearer test_1"
        })
        # May get 403 (no access) or 404 (not found)
        assert response.status_code in [403, 404]


class TestGetPatientConsultations:
    """Tests for retrieving patient consultation history."""

    def test_get_patient_consultations_with_access(self, test_client, db_session):
        """Test getting patient consultations when doctor has access."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13900139444",
            nickname="对话测试患者",
            gender="male",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with test_doctor
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.commit()

        # Get patient consultations
        response = test_client.get(f"/api/doctor/patients/{patient.id}/consultations", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_patient_consultations_no_access(self, test_client, db_session):
        """Test getting consultations when doctor has no access."""
        from app.models.user import User

        # Create a patient with no relationship
        patient = User(
            phone="13900139333",
            nickname="无权限对话患者",
            gender="female",
            is_active=True
        )
        db_session.add(patient)
        db_session.commit()

        # Try to get consultations without access
        response = test_client.get(f"/api/doctor/patients/{patient.id}/consultations", headers={
            "Authorization": "Bearer test_1"
        })
        # Should get 403 Forbidden
        assert response.status_code == 403

    def test_get_patient_consultations_with_limit(self, test_client, db_session):
        """Test getting consultations with custom limit."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13900139222",
            nickname="限制测试患者",
            gender="male",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with test_doctor
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.commit()

        # Get consultations with limit
        response = test_client.get(f"/api/doctor/patients/{patient.id}/consultations?limit=5", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCreateOrder:
    """Tests for creating medical orders."""

    def test_create_order_success(self, test_client, db_session):
        """Test creating a medical order successfully."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13900139111",
            nickname="医嘱测试患者",
            gender="male",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with test_doctor
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.commit()

        # Create medical order
        response = test_client.post("/api/doctor/orders",
            headers={"Authorization": "Bearer test_1"},
            json={
                "patient_id": patient.id,
                "order_type": "medication",
                "title": "阿司匹林",
                "description": "每日服用一次",
                "schedule_type": "daily",
                "start_date": "2026-02-11",
                "reminder_times": ["08:00"]
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == patient.id
        assert data["title"] == "阿司匹林"
        assert data["status"] == "draft"

    def test_create_order_no_access(self, test_client, db_session):
        """Test creating order for patient without access."""
        from app.models.user import User

        # Create a patient with no relationship
        patient = User(
            phone="13900139000",
            nickname="无权限医嘱患者",
            gender="female",
            is_active=True
        )
        db_session.add(patient)
        db_session.commit()

        # Try to create order without access
        response = test_client.post("/api/doctor/orders",
            headers={"Authorization": "Bearer test_1"},
            json={
                "patient_id": patient.id,
                "order_type": "medication",
                "title": "测试医嘱",
                "schedule_type": "once",
                "start_date": "2026-02-11",
                "reminder_times": ["08:00"]
            }
        )
        # Should get 403 Forbidden
        assert response.status_code == 403

    def test_create_order_missing_fields(self, test_client):
        """Test creating order with missing required fields."""
        response = test_client.post("/api/doctor/orders",
            headers={"Authorization": "Bearer test_1"},
            json={
                "patient_id": 1
                # Missing required fields
            }
        )
        assert response.status_code == 422  # Validation error


class TestActivateOrder:
    """Tests for activating medical orders."""

    def test_activate_order_success(self, test_client, db_session):
        """Test activating a medical order successfully."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship
        from app.models.medical_order import MedicalOrder, OrderType, ScheduleType, OrderStatus

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13900138999",
            nickname="激活测试患者",
            gender="male",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with test_doctor
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.flush()

        # Create draft order
        order = MedicalOrder(
            patient_id=patient.id,
            doctor_id=test_doctor.id,
            order_type=OrderType.MEDICATION,
            title="测试医嘱",
            schedule_type=ScheduleType.ONCE,
            start_date=date.today(),
            reminder_times=["08:00"],
            status=OrderStatus.DRAFT
        )
        db_session.add(order)
        db_session.commit()

        # Activate order
        response = test_client.post(f"/api/doctor/orders/{order.id}/activate",
            headers={"Authorization": "Bearer test_1"},
            json={"confirm": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_activate_order_no_confirm(self, test_client):
        """Test activating order without confirmation."""
        response = test_client.post("/api/doctor/orders/1/activate",
            headers={"Authorization": "Bearer test_1"},
            json={"confirm": False}
        )
        assert response.status_code == 400

    def test_activate_order_not_exists(self, test_client):
        """Test activating non-existent order."""
        response = test_client.post("/api/doctor/orders/99999/activate",
            headers={"Authorization": "Bearer test_1"},
            json={"confirm": True}
        )
        assert response.status_code == 404


class TestGetPatientOrders:
    """Tests for retrieving patient medical orders."""

    def test_get_patient_orders_with_access(self, test_client, db_session):
        """Test getting patient orders when doctor has access."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship
        from app.models.medical_order import MedicalOrder, OrderType, ScheduleType, OrderStatus

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13900138888",
            nickname="获取医嘱测试患者",
            gender="female",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with test_doctor
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.flush()

        # Create an order
        order = MedicalOrder(
            patient_id=patient.id,
            doctor_id=test_doctor.id,
            order_type=OrderType.MEDICATION,
            title="测试医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["08:00"],
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()

        # Get patient orders
        response = test_client.get(f"/api/doctor/patients/{patient.id}/orders", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_patient_orders_no_access(self, test_client, db_session):
        """Test getting orders when doctor has no access."""
        from app.models.user import User

        # Create a patient with no relationship
        patient = User(
            phone="13900138777",
            nickname="无权限医嘱患者",
            gender="male",
            is_active=True
        )
        db_session.add(patient)
        db_session.commit()

        # Try to get orders without access
        response = test_client.get(f"/api/doctor/patients/{patient.id}/orders", headers={
            "Authorization": "Bearer test_1"
        })
        # Should get 403 Forbidden
        assert response.status_code == 403

    def test_get_patient_orders_with_status_filter(self, test_client, db_session):
        """Test getting patient orders with status filter."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13900138666",
            nickname="过滤测试患者",
            gender="female",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with test_doctor
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.commit()

        # Get orders with status filter
        response = test_client.get(f"/api/doctor/patients/{patient.id}/orders?status_filter=active", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_patient_orders_invalid_status(self, test_client, db_session):
        """Test getting orders with invalid status filter."""
        from app.models.user import User
        from app.models.doctor_patient_relationship import DoctorPatientRelationship

        # Get or create the test_doctor
        test_doctor = get_test_doctor(db_session)

        # Create test patient
        patient = User(
            phone="13900138555",
            nickname="无效状态测试患者",
            gender="male",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

        # Create relationship with test_doctor
        relationship = DoctorPatientRelationship(
            doctor_id=test_doctor.id,
            patient_id=patient.id,
            relationship_type="primary",
            is_active=True
        )
        db_session.add(relationship)
        db_session.commit()

        # Get orders with invalid status
        response = test_client.get(f"/api/doctor/patients/{patient.id}/orders?status_filter=invalid_status", headers={
            "Authorization": "Bearer test_1"
        })
        assert response.status_code == 400
