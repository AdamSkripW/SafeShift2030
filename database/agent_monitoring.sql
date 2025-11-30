-- Agent Monitoring Table
-- Tracks AI agent usage, performance metrics, and outcomes for analytics and debugging

CREATE TABLE IF NOT EXISTS AgentMetrics (
    MetricId INT PRIMARY KEY AUTO_INCREMENT,
    
    -- Agent identification
    AgentName VARCHAR(100) NOT NULL COMMENT 'Agent identifier (e.g., CrisisDetectionAgent, MicroBreakCoachAgent)',
    ModelVersion VARCHAR(50) DEFAULT 'gpt-4o-mini' COMMENT 'OpenAI model used',
    
    -- User context
    UserId INT NULL COMMENT 'User who triggered the agent (if applicable)',
    ShiftId INT NULL COMMENT 'Related shift (if applicable)',
    
    -- Request/Response metrics
    InputTokens INT NULL COMMENT 'Tokens sent to API',
    OutputTokens INT NULL COMMENT 'Tokens received from API',
    TotalTokens INT GENERATED ALWAYS AS (COALESCE(InputTokens, 0) + COALESCE(OutputTokens, 0)) STORED,
    LatencyMs INT NULL COMMENT 'Response time in milliseconds',
    
    -- Agent-specific output (for CrisisDetectionAgent)
    Severity VARCHAR(20) NULL COMMENT 'Crisis severity: none, low, medium, high, critical',
    ConfidenceScore DECIMAL(3,2) NULL COMMENT 'Agent confidence (0.00-1.00)',
    CrisisDetected BOOLEAN DEFAULT FALSE COMMENT 'True if crisis detected',
    EscalationNeeded BOOLEAN DEFAULT FALSE COMMENT 'True if supervisor notification required',
    
    -- Execution status
    Success BOOLEAN DEFAULT TRUE COMMENT 'True if agent executed without errors',
    ErrorMessage TEXT NULL COMMENT 'Error details if failed',
    FallbackUsed BOOLEAN DEFAULT FALSE COMMENT 'True if safe fallback response returned',
    
    -- Metadata
    RequestPayload JSON NULL COMMENT 'Input data sent to agent (for debugging)',
    ResponsePayload JSON NULL COMMENT 'Full agent response (for audit)',
    
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for fast queries
    INDEX idx_agent_name (AgentName),
    INDEX idx_user_id (UserId),
    INDEX idx_created_at (CreatedAt),
    INDEX idx_severity (Severity),
    INDEX idx_crisis_detected (CrisisDetected),
    INDEX idx_success (Success),
    
    -- Foreign keys
    FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE SET NULL,
    FOREIGN KEY (ShiftId) REFERENCES Shifts(ShiftId) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tracks AI agent invocations for monitoring, analytics, and cost analysis';

-- Sample queries for analytics

-- 1. Agent usage summary (last 7 days)
-- SELECT 
--     AgentName,
--     COUNT(*) as TotalCalls,
--     SUM(CASE WHEN Success = TRUE THEN 1 ELSE 0 END) as SuccessfulCalls,
--     AVG(LatencyMs) as AvgLatencyMs,
--     SUM(TotalTokens) as TotalTokensUsed,
--     AVG(ConfidenceScore) as AvgConfidence
-- FROM AgentMetrics
-- WHERE CreatedAt >= DATE_SUB(NOW(), INTERVAL 7 DAY)
-- GROUP BY AgentName;

-- 2. Crisis detection rate
-- SELECT 
--     DATE(CreatedAt) as Date,
--     COUNT(*) as TotalAnalyses,
--     SUM(CASE WHEN CrisisDetected = TRUE THEN 1 ELSE 0 END) as CrisesDetected,
--     SUM(CASE WHEN Severity = 'critical' THEN 1 ELSE 0 END) as CriticalCases,
--     SUM(CASE WHEN EscalationNeeded = TRUE THEN 1 ELSE 0 END) as Escalations
-- FROM AgentMetrics
-- WHERE AgentName = 'CrisisDetectionAgent'
-- GROUP BY DATE(CreatedAt)
-- ORDER BY Date DESC;

-- 3. User-level crisis history
-- SELECT 
--     u.FirstName,
--     u.LastName,
--     COUNT(*) as TotalAnalyses,
--     SUM(CASE WHEN am.CrisisDetected = TRUE THEN 1 ELSE 0 END) as CrisesDetected,
--     MAX(am.Severity) as HighestSeverity,
--     MAX(am.CreatedAt) as LastAnalysis
-- FROM AgentMetrics am
-- JOIN Users u ON am.UserId = u.UserId
-- WHERE am.AgentName = 'CrisisDetectionAgent'
-- GROUP BY u.UserId
-- ORDER BY CrisesDetected DESC;

-- 4. Performance monitoring (slow queries, errors)
-- SELECT 
--     AgentName,
--     COUNT(*) as FailureCount,
--     AVG(LatencyMs) as AvgLatency,
--     MAX(LatencyMs) as MaxLatency,
--     GROUP_CONCAT(DISTINCT LEFT(ErrorMessage, 100)) as SampleErrors
-- FROM AgentMetrics
-- WHERE Success = FALSE OR LatencyMs > 5000
-- GROUP BY AgentName;

-- 5. Cost estimation (assuming gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output tokens)
-- SELECT 
--     AgentName,
--     SUM(InputTokens) as TotalInputTokens,
--     SUM(OutputTokens) as TotalOutputTokens,
--     ROUND((SUM(InputTokens) * 0.15 / 1000000) + (SUM(OutputTokens) * 0.60 / 1000000), 4) as EstimatedCostUSD
-- FROM AgentMetrics
-- WHERE CreatedAt >= DATE_SUB(NOW(), INTERVAL 30 DAY)
-- GROUP BY AgentName;
