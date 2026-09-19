"""Declared evidence links. Status comes only from a supplied executed test report."""

PREFIX={"core":"tests.test_independent.CoreTests.","task":"tests.test_independent.TaskTests.",
    "schema":"tests.test_independent.ContractTests.","run":"tests.test_runner.RunnerTests.",
    "contract":"tests.test_runtime_contracts.RuntimeContractTests.","extra":"tests.test_extended.ExtendedTests.",
    "long":"tests.test_extended.Scripted32MetricTests.","eval":"tests.test_evaluator.EvaluatorTests.",
    "collection":"tests.test_collection.CollectionTests.","probe":"tests.test_probe32.Probe32Tests.",
    "manifest":"tests.test_manifests.ManifestTests.","boundary":"tests.test_boundaries.BoundaryTests.","freeze":"tests.test_freeze.FreezeTests."}


def names(*entries):return [PREFIX[group]+"test_"+method for group,method in entries]


INVARIANTS={
"I01":("profiles, invariants, replay",names(("run","commit_survives_failed_ACTION_and_replay"),("run","full_scripted_B0_trajectory_and_replay"))),
"I02":("profiles, state, invariants",names(("run","B0_real_episode_record"),("run","B1_B2_exact_one_prep"),("run","B4_full_strong_tracker_no_profile"),("schema","all_frozen_schema_specimens"))),
"I03":("runner._initial_profile, schemas",names(("run","B3_declaration_free_normal_episode"),("run","B4_full_strong_tracker_no_profile"),("schema","all_frozen_schema_specimens"))),
"I04":("profiles.commit, schemas",names(("contract","unknown_return_and_restore"),("run","A01_A03_M07_all_UNKNOWN_not_perfect_calibration"))),
"I05":("profiles.commit, invariants",names(("extra","A04_X02_X04_reject_not_mutate"))),
"I06":("profiles.commit, invariants",names(("extra","F09_rollback_versions_history_monotone"),("extra","F10_scope_strict_subset_and_X03_stale"),("contract","shared_committer_one_sample_allowed"))),
"I07":("profiles.commit",names(("extra","X05_hidden_blind_and_X01_label_blind"),("contract","commit_rejections_and_local_control"))),
"I08":("runner, tool_dispatch, invariants",names(("run","VERIFY_seal_then_tool"),("run","tool_exception_is_infra_not_agent_error"))),
"I09":("runner, invariants",names(("run","F12_wrong_VERIFY_remains_informative_failure"))),
"I10":("runner, schemas, invariants",names(("run","B0_real_episode_record"),("run","DELEGATE_does_not_supply_solo_evidence"),("run","ABSTAIN_null_answer_and_no_tool"))),
"I11":("runner, evaluator, tool_dispatch",names(("run","tool_exception_is_infra_not_agent_error"),("boundary","enforced_tool_timeout_typed_and_no_retry"),("run","F12_wrong_VERIFY_remains_informative_failure"))),
"I12":("calls, prompts",names(("run","F14_repair_sees_no_fresh_context"),("run","F15_second_invalid_no_second_repair"))),
"I13":("runner, invariants, replay",names(("run","commit_survives_failed_ACTION_and_replay"),("long","M06_action_vector_and_A05_text_only"))),
"I14":("state, prompts, schemas",names(("run","A09_hidden_canaries_leave_B4_requests_unchanged"),("boundary","private_schema_error_receipt_history_probe_canaries"),("schema","public_reachable_bundles"))),
"I15":("state, calls, schemas",names(("run","full_scripted_B0_trajectory_and_replay"),("extra","storage_patch_exact_single_removal_and_witness"))),
"I16":("manifest, calibration, tasks",names(("manifest","I16_I18_reproducible_480_separate_splits"),("manifest","I16_previous_calibration_fingerprint_is_regenerated"),("manifest","A11_transfer_latent_duplicate_rejected_before_run"))),
"I17":("tasks, tool_worker, answers",names(("task","F1_independent_random_vectors"),("task","F2_independent_exhaustive_crosscheck"),("task","F03_unique"),("task","F04_ambiguous"),("task","F05_unsat"))),
"I18":("manifest, runner, seed, invariants",names(("manifest","I16_I18_reproducible_480_separate_splits"),("core","seed_exact_preimage"),("contract","PREP_24_paths"))),
"I19":("calls, state, evaluator",names(("eval","accounting_no_double_count_and_unknown"),("run","F14_repair_sees_no_fresh_context"),("run","accepted_PREP_timeout_counts_one_no_free_skip"))),
"I20":("evaluator.rate, opportunity, resource_ratio",names(("eval","M01_four_outcomes"),("eval","M02_tools_and_zero"),("eval","M03_F16_empty_conditional_retains_fixed_TOOL_ITT"),("extra","M08_missing_zero_distinct"))),
"I21":("manifest, runner, evaluator, b4",names(("schema","X11_B4_counts_and_X10_dedup"),("manifest","A11_transfer_latent_duplicate_rejected_before_run"),("run","DELEGATE_does_not_supply_solo_evidence"))),
"I22":("runner.evidence_before, evaluator",names(("extra","I22_earliest_gates_use_only_previous_observations"),("extra","F06_C1_preserve_and_F07_F08_gates"),("long","mode_change_cannot_borrow_old_evidence_response"))),
"I23":("evaluator.bootstrap_pairs, evaluate_dataset",names(("collection","I23_joint_matched_block_and_structural_redundancy"),("collection","duplicates_refused_not_double_n"),("eval","seeded_paired_bootstrap"))),
"I24":("classifier, evaluator",names(("contract","all_19_goldens_runtime"),("contract","R1_E07_HARM_01_counterproductive_missing"),("contract","R1_E07_HARM_01_mixed_missing"),("collection","I24_missing_conditional_not_save_known_fixed_harm")))
}

FIXTURES={
"F01":names(("task","F01_hand_vector")),"F02":names(("task","F02_invalid_tasks")),"F03":names(("task","F03_unique")),"F04":names(("task","F04_ambiguous")),"F05":names(("task","F05_unsat")),
"F06":names(("extra","F06_C1_preserve_and_F07_F08_gates")),"F07":names(("extra","F06_C1_preserve_and_F07_F08_gates"),("contract","shared_committer_one_sample_allowed")),"F08":names(("extra","F06_C1_preserve_and_F07_F08_gates"),("long","M05_post_E_response_grace_target_opportunities")),
"F09":names(("extra","F09_rollback_versions_history_monotone")),"F10":names(("extra","F10_scope_strict_subset_and_X03_stale")),"F11":names(("contract","unknown_return_and_restore")),"F12":names(("run","F12_wrong_VERIFY_remains_informative_failure")),"F13":names(("run","DELEGATE_does_not_supply_solo_evidence")),
"F14":names(("run","F14_repair_sees_no_fresh_context")),"F15":names(("run","F15_second_invalid_no_second_repair"),("run","commit_survives_failed_ACTION_and_replay")),"F16":names(("eval","M03_F16_empty_conditional_retains_fixed_TOOL_ITT")),"F17":names(("eval","accounting_no_double_count_and_unknown")),"F18":names(("freeze","F18_reserved_and_protocol_tuning_rejected")),"F19":names(("probe","PROBE21_labels_never_causal_discrimination")),
"A01":names(("run","A01_A03_M07_all_UNKNOWN_not_perfect_calibration")),"A02":names(("eval","A02_A12_32_episode_controlled_arithmetic")),"A03":names(("run","A01_A03_M07_all_UNKNOWN_not_perfect_calibration")),"A04":names(("extra","A04_X02_X04_reject_not_mutate")),"A05":names(("long","M06_action_vector_and_A05_text_only")),"A06":names(("contract","shared_committer_one_sample_allowed")),"A07":names(("long","A07_never_revise_right_censored")),"A08":names(("contract","commit_rejections_and_local_control")),"A09":names(("run","A09_hidden_canaries_leave_B4_requests_unchanged"),("boundary","private_schema_error_receipt_history_probe_canaries")),"A10":names(("schema","all_frozen_schema_specimens"),("run","F12_wrong_VERIFY_remains_informative_failure")),"A11":names(("manifest","A11_transfer_latent_duplicate_rejected_before_run")),"A12":names(("eval","A02_A12_32_episode_controlled_arithmetic"),("probe","32_next_matched_stop_pending_expiry_and_end_pending")),
"X01":names(("extra","X05_hidden_blind_and_X01_label_blind")),"X02":names(("extra","A04_X02_X04_reject_not_mutate")),"X03":names(("extra","F10_scope_strict_subset_and_X03_stale")),"X04":names(("extra","A04_X02_X04_reject_not_mutate")),"X05":names(("extra","X05_hidden_blind_and_X01_label_blind")),"X06":names(("run","B1_B2_exact_one_prep"),("run","B3_declaration_free_normal_episode"),("freeze","F18_reserved_and_protocol_tuning_rejected")),"X07":names(("run","full_scripted_B0_trajectory_and_replay")),"X08":names(("run","commit_survives_failed_ACTION_and_replay"),("core","store_detects_mutation_and_truncation")),"X09":names(("task","X09_alpha_and_conjunction")),"X10":names(("schema","X11_B4_counts_and_X10_dedup")),"X11":names(("schema","X11_B4_counts_and_X10_dedup")),"X12":names(("contract","all_19_goldens_runtime")),
"M01":names(("eval","M01_four_outcomes")),"M02":names(("eval","M02_tools_and_zero")),"M03":names(("eval","M03_F16_empty_conditional_retains_fixed_TOOL_ITT")),"M04":names(("run","M04_rejected_attempt_not_numeric_distance_denominator")),"M05":names(("long","M05_post_E_response_grace_target_opportunities")),"M06":names(("long","M06_action_vector_and_A05_text_only")),"M07":names(("run","A01_A03_M07_all_UNKNOWN_not_perfect_calibration")),"M08":names(("extra","M08_missing_zero_distinct"))}


def coverage_report(test_report):
    executed={r["test_id"]:r["status"] for r in test_report["executed"]}
    def row(identifier,components,tests):
        missing=[name for name in tests if executed.get(name)!="PASS"]
        return dict(invariant_id=identifier,implementation_component=components,test_ids=tests,
            status="COVERED" if not missing else "NOT_VERIFIED",missing_or_failed=missing,
            failure_type="INFRA_FAILURE_OR_TYPED_CONTRACT_REJECTION",notes="Executable regression coverage, not proof against all possible defects.")
    invariants=[row(k,*v) for k,v in sorted(INVARIANTS.items())]
    fixtures=[dict(fixture_id=k,test_ids=v,status="PASS" if all(executed.get(t)=="PASS" for t in v) else "NOT_VERIFIED") for k,v in sorted(FIXTURES.items())]
    return dict(status="PASS" if all(r["status"]=="COVERED" for r in invariants) and all(r["status"]=="PASS" for r in fixtures) else "FAIL",
        invariants=invariants,fixtures=fixtures,invariant_count=len(invariants),fixture_count=len(fixtures),
        evidence_kind="DESIGN_TEST_VECTOR_NOT_MODEL_RESULT",source="SPEC I01-I24 and Fixture Plan F01-F19/A01-A12/X01-X12/M01-M08")
