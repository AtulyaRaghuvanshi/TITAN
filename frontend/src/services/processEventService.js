/**
 * Process Event Service
 * Converts backend events into user-friendly process transparency messages
 */

class ProcessEventService {
  constructor() {
    this.eventMap = {
      'session_started': {
        message: 'Session initiated',
        category: 'Session',
      },
      'SALES_UPDATE': {
        message: 'Processing loan request',
        category: 'Sales',
      },
      'VERIFICATION_UPDATE': {
        message: 'Verifying customer documents',
        category: 'Verification',
      },
      'UNDERWRITING_DECISION': {
        message: 'Evaluating loan eligibility',
        category: 'Underwriting',
      },
      'SANCTION_GENERATED': {
        message: 'Generating sanction letter',
        category: 'Sanction',
      },
      'preapproved_instant_approval_confirmed': {
        message: 'Pre-approved offer confirmed',
        category: 'Approval',
      },
      'kyc_documents_uploaded': {
        message: 'KYC documents received',
        category: 'Verification',
      },
      'eligibility_evaluated': {
        message: 'Eligibility check completed',
        category: 'Underwriting',
      },
      'loan_approved_after_evaluation': {
        message: 'Loan approved after evaluation',
        category: 'Approval',
      },
      'loan_rejected': {
        message: 'Loan application reviewed',
        category: 'Decision',
      },
    };
  }

  /**
   * Convert backend event to process transparency message
   */
  convertEvent(event) {
    const eventType = event.event_type || event.type;
    const mapping = this.eventMap[eventType];

    if (mapping) {
      return {
        message: mapping.message,
        status: 'completed',
        timestamp: event.timestamp || new Date().toISOString(),
        category: mapping.category,
      };
    }

    // Fallback for unknown events
    return {
      message: eventType || 'Processing...',
      status: 'completed',
      timestamp: event.timestamp || new Date().toISOString(),
      category: 'System',
    };
  }

  /**
   * Generate process steps based on context
   */
  generateStepsFromContext(context) {
    const steps = [];

    if (!context) return steps;

    // Session started
    if (context.session_id) {
      steps.push({
        message: 'Session initiated',
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Session',
      });
    }

    // Customer matching
    if (context.customer_id) {
      steps.push({
        message: 'Customer ID verified',
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Verification',
      });
    } else if (context.is_new_customer) {
      steps.push({
        message: 'New customer profile created',
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Verification',
      });
    }

    // Pre-approved check
    if (context.preapproved_offer) {
      steps.push({
        message: 'Fetching pre-approved offers',
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Sales',
      });
      steps.push({
        message: 'Pre-approved offer found',
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Sales',
      });
    } else if (context.stage === 'DETAILED_EVALUATION') {
      steps.push({
        message: 'No pre-approved offer found',
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Sales',
      });
      steps.push({
        message: 'Initiating detailed evaluation',
        status: 'processing',
        timestamp: new Date().toISOString(),
        category: 'Evaluation',
      });
    }

    // KYC documents
    if (context.kyc_stage) {
      steps.push({
        message: `KYC upload received – ${context.kyc_stage.replace('_', ' ')}`,
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Verification',
      });
    }

    // Evaluation
    if (context.evaluation_result) {
      steps.push({
        message: 'Checking policies.json compliance',
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Underwriting',
      });
      steps.push({
        message: `Decision: ${context.evaluation_result.approved ? 'Approved' : 'Under Review'}`,
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Decision',
      });
    }

    // Sanction
    if (context.sanction_letter_url || context.loan_id) {
      steps.push({
        message: 'Generating sanction letter',
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Sanction',
      });
      steps.push({
        message: 'PDF created and stored',
        status: 'completed',
        timestamp: new Date().toISOString(),
        category: 'Sanction',
      });
    }

    return steps;
  }
}

export default ProcessEventService;

