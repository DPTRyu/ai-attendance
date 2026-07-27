// State Variables
let currentTab = 'dashboard';
let employeesList = [];
let attendanceFilter = 'all';
let editingEmployeeId = null;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    // Set default date to today in attendance form
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('att-date').value = today;

    // Attach Event Listeners
    setupNavigation();
    setupForms();
    setupFilters();
    setupActions();

    // Load initial data
    loadDashboard();
});

// Toast System
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button style="background:none;border:none;color:white;cursor:pointer;font-weight:bold;margin-left:12px;">&times;</button>
    `;
    
    // Close button event
    toast.querySelector('button').addEventListener('click', () => {
        toast.remove();
    });

    container.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Navigation Helper
function setupNavigation() {
    const tabs = [
        { id: 'btn-tab-dashboard', name: 'dashboard', title: 'Dashboard', subtitle: 'Real-time stats and management logs overview.' },
        { id: 'btn-tab-employees', name: 'employees', title: 'Employee Directory', subtitle: 'Register and manage employee profiles.' },
        { id: 'btn-tab-attendance', name: 'attendance', title: 'Attendance Log', subtitle: 'Review clock-in records and approve timesheets.' },
        { id: 'btn-tab-logs', name: 'logs', title: 'AI Operation Audit Trail', subtitle: 'View detailed history of system actions.' }
    ];

    tabs.forEach(tab => {
        const btn = document.getElementById(tab.id);
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Toggle active class in nav
                tabs.forEach(t => document.getElementById(t.id).classList.remove('active'));
                btn.classList.add('active');

                // Switch section
                document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
                document.getElementById(`section-${tab.name}`).classList.add('active');

                // Update headers
                document.getElementById('current-section-title').textContent = tab.title;
                document.getElementById('current-section-subtitle').textContent = tab.subtitle;

                currentTab = tab.name;
                refreshTabData();
            });
        }
    });
}

function refreshTabData() {
    if (currentTab === 'dashboard') {
        loadDashboard();
    } else if (currentTab === 'employees') {
        loadEmployees();
    } else if (currentTab === 'attendance') {
        loadAttendance();
        loadEmployeesDropdown(); // Keep selection list updated
    } else if (currentTab === 'logs') {
        loadLogs();
    }
}

// Fetch Operator Name
function getOperator() {
    return document.getElementById('operator-select').value;
}

// API Headers Helper
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-Operator': getOperator()
    };
}

// Setup Forms Event Listeners
function setupForms() {
    // Employee Form Submission
    const empForm = document.getElementById('employee-form');
    empForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
            id: document.getElementById('emp-id').value.trim(),
            name: document.getElementById('emp-name').value.trim(),
            department: document.getElementById('emp-dept').value.trim(),
            manager_name: document.getElementById('emp-manager').value.trim(),
            email: document.getElementById('emp-email').value.trim()
        };

        try {
            let response;
            if (editingEmployeeId) {
                // Update
                response = await fetch(`/api/v1/employees/${editingEmployeeId}`, {
                    method: 'PUT',
                    headers: getHeaders(),
                    body: JSON.stringify(payload)
                });
            } else {
                // Create
                response = await fetch('/api/v1/employees', {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify(payload)
                });
            }

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to save employee');
            }

            showToast(editingEmployeeId ? 'Employee updated successfully.' : 'Employee registered successfully.', 'success');
            
            // Reset Form state
            cancelEmployeeEdit();
            loadEmployees();

        } catch (error) {
            showToast(error.message, 'error');
        }
    });

    // Employee Edit Cancel Button
    document.getElementById('btn-employee-cancel').addEventListener('click', () => {
        cancelEmployeeEdit();
    });

    // Attendance Form Submission
    const attForm = document.getElementById('attendance-form');
    attForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const empId = document.getElementById('att-employee-id').value;
        const workDate = document.getElementById('att-date').value;
        const startTimeInput = document.getElementById('att-start-time').value;
        const endTimeInput = document.getElementById('att-end-time').value;

        // Construct timestamps
        const startTime = `${workDate}T${startTimeInput}:00`;
        const endTime = endTimeInput ? `${workDate}T${endTimeInput}:00` : null;

        const payload = {
            employee_id: empId,
            work_date: workDate,
            start_time: startTime,
            end_time: endTime
        };

        try {
            const response = await fetch('/api/v1/attendance', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to register attendance');
            }

            showToast('Attendance record logged (Pending approval).', 'success');
            attForm.reset();
            // Restore default date
            document.getElementById('att-date').value = new Date().toISOString().split('T')[0];
            loadAttendance();

        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

// Setup Table Filters (Attendance)
function setupFilters() {
    const filterButtons = document.querySelectorAll('.btn-filter');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            attendanceFilter = btn.getAttribute('data-filter');
            loadAttendance();
        });
    });
}

// Setup Demo Reset, Bulk Approvals, Logs buttons
function setupActions() {
    // Demo Reset Button
    document.getElementById('btn-demo-reset').addEventListener('click', async () => {
        if (confirm('Are you sure you want to delete all data and reset to default seeds?')) {
            try {
                const response = await fetch('/api/v1/demo/reset', {
                    method: 'POST',
                    headers: getHeaders()
                });
                if (!response.ok) throw new Error('Reset failed');
                showToast('Database reset to initial seeds.', 'success');
                refreshTabData();
            } catch (error) {
                showToast(error.message, 'error');
            }
        }
    });

    // Clear Logs Button
    document.getElementById('btn-clear-logs').addEventListener('click', async () => {
        if (confirm('Are you sure you want to clear the audit logs?')) {
            try {
                const response = await fetch('/api/v1/logs', {
                    method: 'DELETE',
                    headers: getHeaders()
                });
                if (!response.ok) throw new Error('Failed to clear logs');
                showToast('Audit trail history cleared.', 'success');
                loadLogs();
            } catch (error) {
                showToast(error.message, 'error');
            }
        }
    });

    // Bulk Approve buttons
    const btnBulkApprove = document.getElementById('btn-bulk-approve');
    const bulkBar = document.getElementById('bulk-exclude-container');
    const btnCancelBulk = document.getElementById('btn-cancel-bulk');
    const btnConfirmBulk = document.getElementById('btn-confirm-bulk');

    btnBulkApprove.addEventListener('click', () => {
        bulkBar.classList.remove('hide');
    });

    btnCancelBulk.addEventListener('click', () => {
        bulkBar.classList.add('hide');
    });

    btnConfirmBulk.addEventListener('click', async () => {
        const approver = document.getElementById('bulk-approver-name').value.trim() || 'System Manager';
        const rawExclude = document.getElementById('bulk-exclude-names').value.trim();
        const excludeList = rawExclude ? rawExclude.split(',').map(name => name.trim()) : [];

        try {
            const response = await fetch('/api/v1/attendance/bulk-approve', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({
                    approver: approver,
                    exclude_employee_names: excludeList
                })
            });

            if (!response.ok) throw new Error('Bulk approval failed');
            const data = await response.json();
            
            showToast(data.message, 'success');
            bulkBar.classList.add('hide');
            refreshStatusViews();
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

// -------------------------------------------------------------
// DATA LOADING FUNCTIONS
// -------------------------------------------------------------

// 1. Dashboard Tab
async function loadDashboard() {
    try {
        const response = await fetch('/api/v1/dashboard');
        if (!response.ok) throw new Error('Failed to fetch dashboard statistics');
        const data = await response.json();

        // Update counts
        document.getElementById('stats-pending-count').textContent = data.pending_approvals;
        document.getElementById('stats-approved-today-count').textContent = data.approved_today;

        // Pending Employee Names
        const namesList = document.getElementById('stats-pending-names');
        namesList.innerHTML = '';
        if (data.pending_employee_names && data.pending_employee_names.length > 0) {
            data.pending_employee_names.forEach(name => {
                const li = document.createElement('li');
                li.className = 'pending-name-item';
                li.textContent = name;
                namesList.appendChild(li);
            });
        } else {
            namesList.innerHTML = '<li class="empty-state">No pending approvals.</li>';
        }

        // Recent Audit logs
        const logsContainer = document.getElementById('stats-recent-logs');
        logsContainer.innerHTML = '';
        if (data.latest_logs && data.latest_logs.length > 0) {
            data.latest_logs.forEach(log => {
                const item = document.createElement('div');
                item.className = 'audit-log-item';
                
                // Format timestamp nicely
                const time = new Date(log.created_at).toLocaleString();
                const resultClass = log.result === 'Success' || log.operation === 'Status Changed'
                    ? 'result-success'
                    : 'result-failure';
                
                item.innerHTML = `
                    <div class="audit-log-meta">
                        <span><span class="audit-log-operator">${log.operator}</span> performed <span class="audit-log-op">${log.operation}</span></span>
                        <span>${time}</span>
                    </div>
                    <div class="audit-log-target">Target: ${log.target} <span class="result-badge ${resultClass}">${log.result}</span></div>
                    ${log.details ? `<div class="audit-log-desc">${log.details}</div>` : ''}
                `;
                logsContainer.appendChild(item);
            });
        } else {
            logsContainer.innerHTML = '<div class="empty-state">No recent logs.</div>';
        }

    } catch (error) {
        showToast(error.message, 'error');
    }
}

// 2. Employees Tab
async function loadEmployees() {
    try {
        const response = await fetch('/api/v1/employees');
        if (!response.ok) throw new Error('Failed to fetch employees');
        employeesList = await response.json();

        const tbody = document.getElementById('employees-table-body');
        tbody.innerHTML = '';

        if (employeesList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No employees found.</td></tr>';
            return;
        }

        employeesList.forEach(emp => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${emp.id}</td>
                <td><strong>${emp.name}</strong></td>
                <td>${emp.department}</td>
                <td>${emp.manager_name || '-'}</td>
                <td>${emp.email}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-action edit-btn" title="Edit Employee">
                            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        </button>
                        <button class="btn-action reject-hover delete-btn" title="Delete Employee">
                            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                        </button>
                    </div>
                </td>
            `;

            // Wire up actions
            tr.querySelector('.edit-btn').addEventListener('click', () => editEmployee(emp));
            tr.querySelector('.delete-btn').addEventListener('click', () => deleteEmployee(emp.id));

            tbody.appendChild(tr);
        });

    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Populate employee select box in attendance form
async function loadEmployeesDropdown() {
    try {
        const response = await fetch('/api/v1/employees');
        if (!response.ok) return;
        const list = await response.json();
        
        const dropdown = document.getElementById('att-employee-id');
        const currentSelection = dropdown.value;
        
        dropdown.innerHTML = '<option value="">-- Choose Employee --</option>';
        list.forEach(emp => {
            const opt = document.createElement('option');
            opt.value = emp.id;
            opt.textContent = `${emp.name} (${emp.id})`;
            dropdown.appendChild(opt);
        });

        // Restore selection if employee still exists
        if (list.some(e => e.id === currentSelection)) {
            dropdown.value = currentSelection;
        }
    } catch (err) {
        console.error(err);
    }
}

function editEmployee(emp) {
    document.getElementById('employee-form-title').textContent = 'Edit Employee';
    document.getElementById('btn-employee-submit').textContent = 'Update Employee';
    document.getElementById('btn-employee-cancel').classList.remove('hide');
    
    // Fill values
    document.getElementById('emp-id').value = emp.id;
    document.getElementById('emp-id').disabled = true; // Cannot edit ID
    document.getElementById('emp-name').value = emp.name;
    document.getElementById('emp-dept').value = emp.department;
    document.getElementById('emp-manager').value = emp.manager_name || '';
    document.getElementById('emp-email').value = emp.email;

    editingEmployeeId = emp.id;
}

function cancelEmployeeEdit() {
    document.getElementById('employee-form-title').textContent = 'Register Employee';
    document.getElementById('btn-employee-submit').textContent = 'Register Employee';
    document.getElementById('btn-employee-cancel').classList.add('hide');
    
    document.getElementById('emp-id').disabled = false;
    document.getElementById('employee-form').reset();
    editingEmployeeId = null;
}

async function deleteEmployee(empId) {
    if (confirm(`Are you sure you want to delete employee ${empId}?`)) {
        try {
            const response = await fetch(`/api/v1/employees/${empId}`, {
                method: 'DELETE',
                headers: getHeaders()
            });

            if (!response.ok) throw new Error('Deletion failed');
            showToast(`Employee ${empId} deleted successfully.`, 'success');
            loadEmployees();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }
}

// 3. Attendance Tab
async function loadAttendance() {
    try {
        let url = '/api/v1/attendance';
        if (attendanceFilter !== 'all') {
            url += `?status=${attendanceFilter}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch attendance');
        const list = await response.json();

        const tbody = document.getElementById('attendance-table-body');
        tbody.innerHTML = '';

        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No attendance records found.</td></tr>`;
            return;
        }

        list.forEach(rec => {
            const tr = document.createElement('tr');
            
            // Format timestamps for display
            const formatTime = (isoStr) => {
                if (!isoStr) return '-';
                try {
                    const date = new Date(isoStr);
                    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                } catch(e) {
                    return isoStr;
                }
            };

            // Badge status
            let badgeClass = 'badge-pending';
            if (rec.status === 'Approved') badgeClass = 'badge-approved';
            if (rec.status === 'Rejected') badgeClass = 'badge-rejected';

            // Show approval buttons only if pending
            let actionsHtml = '';
            if (rec.status === 'Pending') {
                actionsHtml = `
                    <div class="action-buttons">
                        <button class="btn-action approve-hover approve-btn" data-testid="approve-btn-${rec.id}" title="Approve">
                            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><polyline points="20 6 9 17 4 12"/></svg>
                        </button>
                        <button class="btn-action reject-hover reject-btn" data-testid="reject-btn-${rec.id}" title="Reject">
                            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                `;
            } else {
                actionsHtml = `<span style="font-size:0.8rem;color:var(--text-muted);">Locked</span>`;
            }

            tr.innerHTML = `
                <td>
                    <strong>${rec.employee_name || 'Unknown'}</strong><br>
                    <span style="font-size:0.75rem;color:var(--text-secondary);">${rec.employee_id} | ${rec.employee_department || '-'}</span>
                </td>
                <td>${rec.work_date}</td>
                <td>${formatTime(rec.start_time)}</td>
                <td>${formatTime(rec.end_time)}</td>
                <td>
                    <select class="status-select" aria-label="Change status for ${rec.employee_name || rec.employee_id}" data-testid="status-select-${rec.id}">
                        ${['Pending', 'Approved', 'Rejected'].map(status => `<option value="${status}"${status === rec.status ? ' selected' : ''}>${status}</option>`).join('')}
                    </select>
                </td>
                <td>
                    ${rec.approver ? `<strong>${rec.approver}</strong>` : '-'}
                    ${rec.approved_at ? `<br><span style="font-size:0.7rem;color:var(--text-muted);">${new Date(rec.approved_at).toLocaleDateString()}</span>` : ''}
                </td>
                <td>${actionsHtml}</td>
            `;

            // Wire up actions
            if (rec.status === 'Pending') {
                tr.querySelector('.approve-btn').addEventListener('click', () => approveRecord(rec.id));
                tr.querySelector('.reject-btn').addEventListener('click', () => rejectRecord(rec.id));
            }
            tr.querySelector('.status-select').addEventListener('change', (event) => changeRecordStatus(rec.id, event.target));

            tbody.appendChild(tr);
        });

    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function changeRecordStatus(id, select) {
    const nextStatus = select.value;
    select.disabled = true;
    try {
        const response = await fetch(`/api/v1/attendance/${id}/status`, {
            method: 'PATCH',
            headers: getHeaders(),
            body: JSON.stringify({ status: nextStatus })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to change attendance status');
        }
        showToast(`Attendance status changed to ${nextStatus}.`, 'success');
        await refreshStatusViews();
    } catch (error) {
        showToast(error.message, 'error');
        await loadAttendance();
    } finally {
        select.disabled = false;
    }
}

async function refreshStatusViews() {
    await Promise.all([loadAttendance(), loadDashboard(), loadLogs()]);
}

async function approveRecord(id) {
    try {
        const response = await fetch(`/api/v1/attendance/${id}/approve`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ approver: getOperator() })
        });

        if (!response.ok) throw new Error('Failed to approve record');
        showToast('Attendance approved.', 'success');
        refreshStatusViews();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function rejectRecord(id) {
    try {
        const response = await fetch(`/api/v1/attendance/${id}/reject`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ approver: getOperator() })
        });

        if (!response.ok) throw new Error('Failed to reject record');
        showToast('Attendance rejected.', 'success');
        refreshStatusViews();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// 4. Audit Logs Tab
async function loadLogs() {
    try {
        const response = await fetch('/api/v1/logs');
        if (!response.ok) throw new Error('Failed to fetch audit logs');
        const list = await response.json();

        const tbody = document.getElementById('logs-table-body');
        tbody.innerHTML = '';

        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No audit logs found.</td></tr>';
            return;
        }

        list.forEach(log => {
            const tr = document.createElement('tr');
            const time = new Date(log.created_at).toLocaleString();

            tr.innerHTML = `
                <td style="font-family:monospace;font-size:0.8rem;white-space:nowrap;">${time}</td>
                <td><span class="audit-log-operator">${log.operator}</span></td>
                <td><strong>${log.operation}</strong></td>
                <td><code>${log.target}</code></td>
                <td><span class="result-badge ${log.result === 'Success' ? 'result-success' : 'result-failure'}">${log.result}</span></td>
                <td><span style="font-size:0.85rem;color:var(--text-secondary);">${log.details || '-'}</span></td>
            `;

            tbody.appendChild(tr);
        });

    } catch (error) {
        showToast(error.message, 'error');
    }
}
