///////////////////////////////////////////////////////////////////////////////
// BSD 3-Clause License
//
// Copyright (C) 2018-2019, LAAS-CNRS
// Copyright note valid unless otherwise stated in individual files.
// All rights reserved.
///////////////////////////////////////////////////////////////////////////////

#ifndef CROCODDYL_MULTIBODY_ACTIONS_IMPULSE_FWDDYN_HPP_
#define CROCODDYL_MULTIBODY_ACTIONS_IMPULSE_FWDDYN_HPP_

#include "crocoddyl/core/action-base.hpp"
#include "crocoddyl/multibody/states/multibody.hpp"
#include "crocoddyl/multibody/actuations/floating-base.hpp"
#include "crocoddyl/multibody/impulses/multiple-impulses.hpp"
#include "crocoddyl/multibody/costs/cost-sum.hpp"
#include <pinocchio/multibody/data.hpp>

namespace crocoddyl {

class ActionModelImpulseFwdDynamics : public ActionModelAbstract {
 public:
  ActionModelImpulseFwdDynamics(StateMultibody& state, ImpulseModelMultiple& impulses, CostModelSum& costs,
                                const double& r_coeff = 0., const double& JMinvJt_damping = 0.,
                                const bool& enable_force = false);
  ~ActionModelImpulseFwdDynamics();

  void calc(const boost::shared_ptr<ActionDataAbstract>& data, const Eigen::Ref<const Eigen::VectorXd>& x,
            const Eigen::Ref<const Eigen::VectorXd>& u);
  void calcDiff(const boost::shared_ptr<ActionDataAbstract>& data, const Eigen::Ref<const Eigen::VectorXd>& x,
                const Eigen::Ref<const Eigen::VectorXd>& u, const bool& recalc = true);
  boost::shared_ptr<ActionDataAbstract> createData();

  ImpulseModelMultiple& get_impulses() const;
  CostModelSum& get_costs() const;
  pinocchio::Model& get_pinocchio() const;
  const Eigen::VectorXd& get_armature() const;
  const double& get_restitution_coefficient() const;
  const double& get_damping_factor() const;

  void set_armature(const Eigen::VectorXd& armature);
  void set_restitution_coefficient(const double& r_coeff);
  void set_damping_factor(const double& damping);

 private:
  ImpulseModelMultiple& impulses_;
  CostModelSum& costs_;
  pinocchio::Model& pinocchio_;
  bool with_armature_;
  Eigen::VectorXd armature_;
  double r_coeff_;
  double JMinvJt_damping_;
  bool enable_force_;
  pinocchio::Motion gravity_;
};

struct ActionDataImpulseFwdDynamics : public ActionDataAbstract {
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW

  template <typename Model>
  explicit ActionDataImpulseFwdDynamics(Model* const model)
      : ActionDataAbstract(model),
        pinocchio(pinocchio::Data(model->get_pinocchio())),
        vnone(model->get_state().get_nv()),
        Kinv(model->get_state().get_nv() + model->get_impulses().get_ni(),
             model->get_state().get_nv() + model->get_impulses().get_ni()),
        Gx(model->get_impulses().get_ni(), model->get_state().get_ndx()),
        Gu(model->get_impulses().get_ni(), model->get_nu()) {
    impulses = model->get_impulses().createData(&pinocchio);
    costs = model->get_costs().createData(&pinocchio);
    costs->shareMemory(this);
    vnone.fill(0);
    Kinv.fill(0);
    Gx.fill(0);
    Gu.fill(0);
  }

  pinocchio::Data pinocchio;
  boost::shared_ptr<ImpulseDataMultiple> impulses;
  boost::shared_ptr<CostDataSum> costs;
  Eigen::VectorXd vnone;
  Eigen::MatrixXd Kinv;
  Eigen::MatrixXd Gx;
  Eigen::MatrixXd Gu;
};

}  // namespace crocoddyl

#endif  // CROCODDYL_MULTIBODY_ACTIONS_IMPULSE_FWDDYN_HPP_
