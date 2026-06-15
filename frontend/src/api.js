const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function sendMessage(customerId, text, context) {
  const endpoint = `${API_BASE_URL}/chat`;
  const body = {
    customer_id: customerId,
    text: text,
    context: context || null,
  };
  
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

export async function uploadSalarySlip(customerId, file) {
  const endpoint = `${API_BASE_URL}/files/upload-salary-slip?customer_id=${encodeURIComponent(customerId)}`;
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(endpoint, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

export async function getCustomers() {
  // For demo, return hardcoded customer list
  // In production, this would fetch from an API
  return [
    { customer_id: 'C001', name: 'Aarav Mehta' },
    { customer_id: 'C002', name: 'Ritika Singh' },
    { customer_id: 'C003', name: 'Vikram Reddy' },
    { customer_id: 'C004', name: 'Priya Sharma' },
    { customer_id: 'C005', name: 'Rahul Kapoor' },
    { customer_id: 'C006', name: 'Ananya Patel' },
    { customer_id: 'C007', name: 'Karan Malhotra' },
    { customer_id: 'C008', name: 'Sneha Iyer' },
    { customer_id: 'C009', name: 'Aditya Joshi' },
    { customer_id: 'C010', name: 'Meera Desai' },
    { customer_id: 'C011', name: 'Rohan Agarwal' },
    { customer_id: 'C012', name: 'Divya Nair' },
  ];
}

export async function getEvents(customerId) {
  const response = await fetch(`${API_BASE_URL}/events/${customerId}`);
  if (!response.ok) {
    return [];
  }
  const data = await response.json();
  return data.events || [];
}

export async function sendEmailOtp(email) {
  const response = await fetch(`${API_BASE_URL}/otp/send-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
}

export async function verifyEmailOtp(email, code) {
  const response = await fetch(`${API_BASE_URL}/otp/verify-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code }),
  });
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
  return await response.json();
}

