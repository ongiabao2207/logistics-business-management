export const ROLES = {
  SALE: "ROLE_SALE",
  OPERATION: "ROLE_OPERATION",
  ACCOUNTANT: "ROLE_ACCOUNTANT",
  LEGAL: "ROLE_LEGAL",
  DIRECTOR: "ROLE_DIRECTOR",
  ADMIN: "ROLE_ADMIN",
};

export const ROLE_LABELS = {
  [ROLES.SALE]: "Nhân viên kinh doanh",
  [ROLES.OPERATION]: "Nhân viên khai thác",
  [ROLES.ACCOUNTANT]: "Nhân viên kế toán",
  [ROLES.LEGAL]: "Nhân viên pháp chế",
  [ROLES.DIRECTOR]: "Ban giám đốc",
  [ROLES.ADMIN]: "Quản trị viên",
};

export const MODULE_ROLES = {
  identity: [ROLES.ADMIN],
  customers: [ROLES.SALE],
  contracts: [ROLES.SALE, ROLES.LEGAL, ROLES.DIRECTOR, ROLES.ACCOUNTANT],
  prices: [ROLES.SALE, ROLES.ACCOUNTANT, ROLES.LEGAL, ROLES.DIRECTOR],
  production: [ROLES.OPERATION, ROLES.ACCOUNTANT],
  payments: [ROLES.ACCOUNTANT, ROLES.DIRECTOR, ROLES.LEGAL],
  approvals: [ROLES.SALE, ROLES.ACCOUNTANT, ROLES.LEGAL, ROLES.DIRECTOR],
};

export function hasRole(user, allowedRoles) {
  return Boolean(user?.role && allowedRoles.includes(user.role));
}

export const REVIEW_ROLES = [ROLES.LEGAL, ROLES.DIRECTOR];
