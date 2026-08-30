export const dashboardApi = {
  async getSummary() {
    return {
      activeContracts: 0,
      pendingApprovals: 0,
      lockedPeriods: 0,
      openPayments: 0,
    };
  },
};
