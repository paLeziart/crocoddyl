from crocoddyl import StatePinocchio, CostModelSum
from crocoddyl import DifferentialActionModelNumDiff
from crocoddyl import m2a, a2m, absmax, absmin
from crocoddyl import loadTalosArm
from testutils import assertNumDiff, NUMDIFF_MODIFIER
import numpy as np
from numpy.linalg import norm
import pinocchio
from pinocchio.utils import rand


class DifferentialActionModelActuated:
    '''Unperfect class written to validate the actuation model. Do not use except for tests. '''
    def __init__(self,pinocchioModel,actuationModel):
        self.pinocchio = pinocchioModel
        self.actuation = actuationModel
        self.State = StatePinocchio(self.pinocchio)
        self.costs = CostModelSum(self.pinocchio)
        self.nq,self.nv = self.pinocchio.nq, self.pinocchio.nv
        self.nx = self.State.nx
        self.ndx = self.State.ndx
        self.nout = self.nv
        self.nu = self.actuation.nu
        self.unone = np.zeros(self.nu)
    @property
    def ncost(self): return self.costs.ncost
    def createData(self): return DifferentialActionDataActuated(self)
    def calc(model,data,x,u=None):
        if u is None: u=model.unone
        nx,nu,nq,nv,nout = model.nx,model.nu,model.nq,model.nv,model.nout
        q = a2m(x[:nq])
        v = a2m(x[-nv:])
        tauq = a2m(model.actuation.calc(data.actuation,x,u))
        data.xout[:] = pinocchio.aba(model.pinocchio,data.pinocchio,q,v,tauq).flat
        pinocchio.forwardKinematics(model.pinocchio,data.pinocchio,q,v)
        pinocchio.updateFramePlacements(model.pinocchio,data.pinocchio)
        data.cost = model.costs.calc(data.costs,x,u)
        return data.xout,data.cost

    def calcDiff(model,data,x,u=None,recalc=True):
        if u is None: u=model.unone
        if recalc: xout,cost = model.calc(data,x,u)
        nx,ndx,nu,nq,nv,nout = model.nx,model.State.ndx,model.nu,model.nq,model.nv,model.nout
        q = a2m(x[:nq])
        v = a2m(x[-nv:])
        tauq = a2m(data.actuation.a)
        pinocchio.computeABADerivatives(model.pinocchio,data.pinocchio,q,v,tauq)
        da_dq = data.pinocchio.ddq_dq
        da_dv = data.pinocchio.ddq_dv
        da_dact = data.pinocchio.Minv

        dact_dx = data.actuation.Ax
        dact_du = data.actuation.Au
        
        data.Fx[:,:nv] = da_dq
        data.Fx[:,nv:] = da_dv
        data.Fx += np.dot(da_dact,dact_dx)
        data.Fu[:,:]   = np.dot(da_dact,dact_du)

        pinocchio.computeJointJacobians(model.pinocchio,data.pinocchio,q)
        pinocchio.updateFramePlacements(model.pinocchio,data.pinocchio)
        model.costs.calcDiff(data.costs,x,u,recalc=False)

        return data.xout,data.cost

class DifferentialActionDataActuated:
    def __init__(self,model):
        self.pinocchio = model.pinocchio.createData()
        self.actuation = model.actuation.createData(self.pinocchio)
        self.costs = model.costs.createData(self.pinocchio)
        self.cost = np.nan
        self.xout = np.zeros(model.nout)
        nx,nu,ndx,nq,nv,nout = model.nx,model.nu,model.State.ndx,model.nq,model.nv,model.nout
        self.F = np.zeros([ nout,ndx+nu ])
        self.costResiduals = self.costs.residuals
        self.Fx = self.F[:,:ndx]
        self.Fu = self.F[:,-nu:]
        self.Lx  = self.costs.Lx
        self.Lu  = self.costs.Lu
        self.Lxx = self.costs.Lxx
        self.Lxu = self.costs.Lxu
        self.Luu = self.costs.Luu
        self.Rx  = self.costs.Rx
        self.Ru  = self.costs.Ru

## Loading Talos arm with FF TODO use a bided or quadruped
# -----------------------------------------------------------------------------
robot = loadTalosArm(freeFloating=True)

qmin = robot.model.lowerPositionLimit; qmin[:7]=-1; robot.model.lowerPositionLimit = qmin
qmax = robot.model.upperPositionLimit; qmax[:7]= 1; robot.model.upperPositionLimit = qmax

rmodel = robot.model
rdata = rmodel.createData()




## Free floating actuation model
# -----------------------------------------------------------------------------
from crocoddyl import ActuationModelFreeFloating

actModel = ActuationModelFreeFloating(rmodel)
model = DifferentialActionModelActuated(rmodel,actModel)
data  = model.createData()

q = pinocchio.randomConfiguration(rmodel)
v = rand(rmodel.nv)
x = m2a(np.concatenate([q,v]))
u = m2a(rand(rmodel.nv-6))
model.calcDiff(data,x,u)

mnum = DifferentialActionModelNumDiff(model)
dnum = mnum.createData()
mnum.calcDiff(dnum,x,u)
assertNumDiff(data.Fx, dnum.Fx, NUMDIFF_MODIFIER*mnum.disturbance) # threshold was 2.7e-2, is now 2.11e-4 (see assertNumDiff.__doc__)
assertNumDiff(data.Fu, dnum.Fu, NUMDIFF_MODIFIER*mnum.disturbance) # threshold was 7e-3, is now 2.11e-4 (see assertNumDiff.__doc__)
