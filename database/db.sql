-- SafeShift 2030 Database Schema
-- With Authentication & Hospital Admin Support

CREATE DATABASE IF NOT EXISTS safeshift_2030;
USE safeshift_2030;

-- ============================================
-- 1. USERS TABLE (Healthcare Workers)
-- ============================================
CREATE TABLE Users (
    UserId INT AUTO_INCREMENT PRIMARY KEY,
    Email VARCHAR(255) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    FirstName VARCHAR(100) NOT NULL,
    LastName VARCHAR(100) NOT NULL,
    Role ENUM('nurse', 'doctor', 'student') NOT NULL,
    Department VARCHAR(100) NOT NULL,
    Hospital VARCHAR(100) NOT NULL,
    HospitalId INT,
    ProfilePictureUrl VARCHAR(500),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    IsActive BOOLEAN DEFAULT TRUE,
    INDEX (Email),
    INDEX (HospitalId)
);

-- ============================================
-- 2. HOSPITALS TABLE (Institutions)
-- ============================================
CREATE TABLE Hospitals (
    HospitalId INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL UNIQUE,
    City VARCHAR(100) NOT NULL,
    Country VARCHAR(100) NOT NULL,
    ContactEmail VARCHAR(255),
    PhoneNumber VARCHAR(20),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Add Foreign Key depois
ALTER TABLE Users 
ADD CONSTRAINT FK_Users_Hospitals 
FOREIGN KEY (HospitalId) REFERENCES Hospitals(HospitalId) ON DELETE SET NULL;

-- ============================================
-- 3. HOSPITAL ADMINS TABLE
-- ============================================
-- Osoba v nemocnici, ktorá sleduje zdravie zamestnancov
CREATE TABLE HospitalAdmins (
    AdminId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    HospitalId INT NOT NULL,
    Role ENUM('wellness_manager', 'hr_manager', 'hospital_admin') NOT NULL,
    PermissionsViewAll BOOLEAN DEFAULT TRUE,
    PermissionsEditShifts BOOLEAN DEFAULT FALSE,
    PermissionsAssignTimeOff BOOLEAN DEFAULT TRUE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    FOREIGN KEY (HospitalId) REFERENCES Hospitals(HospitalId) ON DELETE CASCADE,
    UNIQUE KEY (UserId, HospitalId),
    INDEX (HospitalId)
);

-- ============================================
-- 4. SHIFTS TABLE (Shift Records)
-- ============================================
CREATE TABLE Shifts (
    ShiftId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    ShiftDate DATE NOT NULL,
    HoursSleptBefore INT NOT NULL CHECK (HoursSleptBefore >= 0 AND HoursSleptBefore <= 24),
    ShiftType ENUM('day', 'night') NOT NULL,
    ShiftLengthHours INT NOT NULL CHECK (ShiftLengthHours >= 1 AND ShiftLengthHours <= 24),
    PatientsCount INT NOT NULL CHECK (PatientsCount >= 0),
    StressLevel INT NOT NULL CHECK (StressLevel >= 1 AND StressLevel <= 10),
    ShiftNote TEXT,
    
    -- Computed by backend
    SafeShiftIndex INT NOT NULL DEFAULT 0 CHECK (SafeShiftIndex >= 0 AND SafeShiftIndex <= 100),
    Zone ENUM('green', 'yellow', 'red') NOT NULL DEFAULT 'green',
    AiExplanation TEXT,
    AiTips TEXT,
    
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    INDEX (UserId, ShiftDate),
    INDEX (Zone)
);

-- ============================================
-- 5. TIME OFF REQUESTS TABLE
-- ============================================
-- Správca zdravia môže prideľovať voľno na základe burnout risk
CREATE TABLE TimeOffRequests (
    TimeOffId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    Reason ENUM('rest_recovery', 'burnout_risk', 'personal', 'admin_assigned') NOT NULL,
    AssignedBy INT,  -- AdminId who assigned it
    Status ENUM('pending', 'approved', 'rejected', 'taken') NOT NULL DEFAULT 'pending',
    Notes TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    FOREIGN KEY (AssignedBy) REFERENCES HospitalAdmins(AdminId) ON DELETE SET NULL,
    INDEX (UserId, Status),
    INDEX (StartDate)
);

-- ============================================
-- 6. BURNOUT ALERTS TABLE
-- ============================================
-- Sledovanie varovaní pre správcov
CREATE TABLE BurnoutAlerts (
    AlertId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    AlertType ENUM('chronic_low_sleep', 'consecutive_nights', 'high_stress_pattern', 'declining_health') NOT NULL,
    Severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    Description TEXT,
    IsResolved BOOLEAN DEFAULT FALSE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ResolvedAt TIMESTAMP NULL,
    
    FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    INDEX (UserId, IsResolved),
    INDEX (Severity)
);

-- ============================================
-- 7. SESSIONS TABLE (Authentication)
-- ============================================
CREATE TABLE Sessions (
    SessionId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    Token VARCHAR(500) NOT NULL UNIQUE,
    ExpiresAt TIMESTAMP NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    IpAddress VARCHAR(50),
    UserAgent VARCHAR(500),
    
    FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE,
    INDEX (Token),
    INDEX (UserId, ExpiresAt)
);

-- ============================================
-- TEST DATA
-- ============================================

-- Hospital
INSERT INTO Hospitals (Name, City, Country, ContactEmail) VALUES
('University Hospital Košice', 'Košice', 'Slovakia', 'info@uhkosice.sk');

-- Healthcare Workers
INSERT INTO Users (Email, PasswordHash, FirstName, LastName, Role, Department, Hospital, HospitalId) VALUES
('maria.kovacs@uhkosice.sk', 'hashed_password_1', 'Mária', 'Kovács', 'nurse', 'ICU', 'University Hospital Košice', 1),
('peter.horvath@uhkosice.sk', 'hashed_password_2', 'Peter', 'Horváth', 'doctor', 'Surgery', 'University Hospital Košice', 1),
('jana.markova@uhkosice.sk', 'hashed_password_3', 'Jana', 'Marková', 'student', 'Internal Medicine', 'University Hospital Košice', 1);

-- Hospital Admin (Wellness Manager)
INSERT INTO HospitalAdmins (UserId, HospitalId, Role, PermissionsViewAll, PermissionsEditShifts, PermissionsAssignTimeOff) VALUES
(1, 1, 'wellness_manager', TRUE, FALSE, TRUE);

-- Shifts
INSERT INTO Shifts (UserId, ShiftDate, HoursSleptBefore, ShiftType, ShiftLengthHours, PatientsCount, StressLevel, ShiftNote, SafeShiftIndex, Zone, AiExplanation, AiTips) VALUES
(2, '2025-11-28', 4, 'night', 12, 18, 8, 'Two critical patients, short staff', 78, 'red', 'Your SafeShift Index is in the red zone mainly because you slept only 4 hours...', '• Prioritize sleep...\n• Process difficult moments...'),
(2, '2025-11-27', 6, 'day', 8, 15, 6, 'Normal day', 42, 'yellow', 'You are on the edge...', '• Take a 20-minute break...\n• Hydration...'),
(3, '2025-11-28', 7, 'day', 8, 10, 5, 'Quiet morning', 28, 'green', 'Safe zone', '• Maintain this pace...');

-- Time Off Request (Admin assigned due to burnout)
INSERT INTO TimeOffRequests (UserId, StartDate, EndDate, Reason, AssignedBy, Status, Notes) VALUES
(2, '2025-12-01', '2025-12-02', 'burnout_risk', 1, 'approved', 'Red zone pattern detected - 3 consecutive nights with low sleep');

-- Burnout Alert
INSERT INTO BurnoutAlerts (UserId, AlertType, Severity, Description) VALUES
(2, 'consecutive_nights', 'high', 'Peter had 3 consecutive night shifts with less than 5 hours of sleep before each shift');
