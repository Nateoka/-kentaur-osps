"""Build static design schemas/dictionary only. NOT a benchmark runtime.

No task generation, solver, evaluator, model calls or simulated results.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://mrab.example.invalid/r1/0.2.1/'
NAMES = ['r1_config','r1_self_profile','r1_episode_record','r1_reflexive_record','r1_trajectory']

def ref(file, name=None):
    return {'$ref': BASE+file+'.schema.json'+('#/$defs/'+name if name else '')}
def fld(schema, description):
    return {**copy.deepcopy(schema), 'description': description}
def obj(properties, description):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False, description=description)
def arr(items, minimum=0, maximum=None, unique=False):
    d=dict(type='array',items=items,minItems=minimum)
    if maximum is not None:d['maxItems']=maximum
    if unique:d['uniqueItems']=True
    return d
def enum(*values):return dict(type='string',enum=list(values))
def nullable(value):return {'anyOf':[value,{'type':'null'}]}
def st(maximum=240):return dict(type='string',minLength=1,maxLength=maximum)
def integer(lo=0,hi=None):
    d=dict(type='integer',minimum=lo)
    if hi is not None:d['maximum']=hi
    return d
NUM=dict(type='number',minimum=0)
PROB=dict(type='number',minimum=0,maximum=1)
BOOL=dict(type='boolean')
ID=dict(type='string',pattern='^[a-zA-Z0-9_:.-]{1,96}$')
SHA=dict(type='string',pattern='^[0-9a-f]{64}$')
C=lambda name:ref('r1_config',name)
P=lambda name:ref('r1_self_profile',name)
E=lambda name:ref('r1_episode_record',name)
R=lambda name:ref('r1_reflexive_record',name)
T=lambda name:ref('r1_trajectory',name)

def make():
    d={
        'architecture':enum('B0','B1','B2','B3','B4','B5'),
        'profile_condition':enum('C0','C1','C2','C3','C4'),
        'family':enum('SYMBOLIC_PIPELINE','RULE_GRID'),
        'action':enum('SOLO','VERIFY','DELEGATE','ABSTAIN'),
        'claim_status':enum('ACTIVE','QUESTIONED','REVISED','NARROWED','UNKNOWN'),
        'confidence':enum('LOW','MEDIUM','HIGH','UNSPECIFIED'),
        'split':enum('CALIBRATION_SEARCH','CALIBRATION_CONFIRM','MAIN','TRANSFER'),
        'phase':enum('INITIAL_EXPOSURE','EVIDENCE_ACCUMULATION','ADAPTATION','TRANSFER','SMOKE_MAIN','SMOKE_TRANSFER'),
        'locus':enum('SELF_CAPABILITY','TASK_VARIATION','CONTEXT','TOOL','UNKNOWN'),
        'probe_type':enum('NONE','VERIFY_CURRENT','SOLO_CURRENT','VERIFY_NEXT_MATCHED'),
        'interval':obj({'lower':fld(PROB,'Нижняя граница probability claim, не confidence interval.'),
                        'upper':fld(PROB,'Верхняя граница; I04 дополнительно требует lower≤upper.')},'Ordered probability interval; comparison is a semantic invariant.'),
        'scope':obj({'scope_id':fld(ID,'Непрозрачный идентификатор области; не HIGH/MID label.'),
                     'task_family':fld(C('family'),'Семейство capability, не evaluator target role.'),
                     'difficulty_scope':fld(arr(ID,1,20,True),'Допустимые difficulty IDs из sealed configuration.'),
                     'context_condition':fld(arr(ID,1,20,True),'Непустое множество применимых public context IDs.'),
                     'tool_condition':fld({'const':'SOLO_NO_TOOL'},'Capability относится к самостоятельному решению без инструмента.')},'Явная область claim; subset и restore проверяются по I01–I07.'),
    }
    def op(kind, props):return obj({'op':fld({'const':kind},'Операция F1.'),**props},'Одна типизированная операция F1; индексы дополнительно проверяются относительно n.')
    index=lambda s:fld(integer(0,7),s)
    d['operation']={'oneOf':[
        op('ADD',{'index':index('Изменяемая координата, zero-based.'),'value':fld({'type':'integer','minimum':-9,'maximum':9,'not':{'const':0}},'Ненулевое слагаемое.')}),
        op('MULTIPLY',{'index':index('Изменяемая координата.'),'value':fld({'type':'integer','enum':[-3,-2,-1,2,3]},'Множитель, исключены 0 и 1.')}),
        op('SWAP',{'left':index('Первая координата.'),'right':index('Вторая координата; distinct от left по G02.')}),
        op('ROTATE',{'steps':fld({'type':'integer','minimum':-7,'maximum':7,'not':{'const':0}},'Right shift; абсолютное значение меньше n по G02.')}),
        op('MOD',{'index':index('Изменяемая координата.'),'modulus':fld(integer(2,11),'Положительный modulus, результат Euclidean remainder.')})]}
    d['probe_prediction']=obj({'locus':fld(C('locus'),'Одна из заранее заявленных альтернатив.'),
        'observable_pattern':fld(enum('SOLO_SUCCESS','SOLO_FAILURE','MATCHED_OUTCOMES_AGREE','MATCHED_OUTCOMES_DIFFER','UNSPECIFIED'),
                                 'Предсказанное публичное различие; это не hidden mechanism.'),
        'if_not_observed':fld(enum('QUESTION_THIS_LOCUS','KEEP_UNKNOWN'),'Судьба гипотезы при несовпадении, не автоматический profile commit.')},
        'Prospective decision interface; не chain-of-thought.')
    d['symbolic_spec']=obj({'family':fld({'const':'SYMBOLIC_PIPELINE'},'Discriminator DSL.'),
        'initial':fld(arr({'type':'integer','minimum':-20,'maximum':20},2,8),'Начальный вектор.'),
        'operations':fld(arr(C('operation'),1,40),'Упорядоченная программа.')},'F1 spec без answer/seed/calibration metadata.')
    d['atom']=obj({'entity':fld(ID,'Entity ID из spec.entities.'),'property':fld(ID,'Property ID из spec.properties.'),
                   'value':fld(ID,'Value ID именно указанного property.')},'Атом равенства RULE_GRID.')
    d['constraint']={'oneOf':[obj({'kind':fld({'const':kind},'Тип логического constraint.'),
        **({'atom':fld(C('atom'),'Проверяемый atom.')} if kind in ['EQ','NEQ'] else {
            'left':fld(C('atom'),'Левый atom.'),'right':fld(C('atom'),'Правый atom.')})},'Логическая формула G03.') for kind in ['EQ','NEQ','IMPLIES','XOR']]}
    d['grid_spec']=obj({'family':fld({'const':'RULE_GRID'},'Discriminator DSL.'),
        'entities':fld(arr(ID,2,5,True),'Уникальные entity IDs.'),
        'properties':fld(arr(obj({'property_id':fld(ID,'Уникальный property ID.'),
                                  'values':fld(arr(ID,2,5,True),'Values; число равно числу entities по G03.')},'Одна bijective property.'),1,3),'Properties с уникальными IDs.'),
        'constraints':fld(arr(C('constraint'),0,60),'Конъюнкция ограничений; уникальность решения проверяет solver.')},'F2 spec; schema допускает intentional ambiguous fixtures, не легализуя их для primary run.')
    d['task_spec']={'oneOf':[C('symbolic_spec'),C('grid_spec')]}
    d['answer']={'oneOf':[
        obj({'family':fld({'const':'SYMBOLIC_PIPELINE'},'Тип ответа.'),'result':fld(arr({'type':'integer'},2,8),'Конечный вектор длины n.')},'Canonical F1 answer.'),
        obj({'family':fld({'const':'RULE_GRID'},'Тип ответа.'),'result':fld(arr(obj({
            'entity_id':fld(ID,'Entity ID строки.'),'assignments':fld(arr(obj({'property_id':fld(ID,'Property ID.'),
                'value_id':fld(ID,'Выбранное значение.')},'Одна ячейка assignment.'),1,3),'Все properties, sorted by property_id.')},'Одна entity, sorted by entity_id.'),2,5),'Полное решение grid; exact bijection и полнота по G03.')},'Canonical F2 answer.')]}
    d['task_view']=obj({'task_id':fld(ID,'Opaque ID, без split/condition/band.'),'task_family':fld(C('family'),'Видимое family.'),
        'scope_id':fld(ID,'Видимый scope ID для локального claim.'),'difficulty_scope':fld(ID,'ID текущего difficulty tuple.'),
        'context_condition':fld(ID,'Видимое условие контекста.'),'spec':fld(C('task_spec'),'Полный DSL, без ground truth.'),
        'surface_text':fld(st(16000),'Answer-free deterministic rendering текущего DSL.')},'Единственное agent-facing представление задачи.')
    d['action_record']=obj({'action':fld(C('action'),'Выбранный реальный action.'),'solo_answer':fld(nullable(C('answer')),'Обязателен для SOLO/VERIFY; null для DELEGATE/ABSTAIN.'),
        'confidence':fld(C('confidence'),'Категориальный self-report, не probability.')},'ACTION output, sealed before tools.')
    d['action_record']['allOf']=[{'if':{'properties':{'action':{'enum':['SOLO','VERIFY']}}},
        'then':{'properties':{'solo_answer':C('answer')}},'else':{'properties':{'solo_answer':{'type':'null'}}}}]
    d['tracker_state']=obj({'scope_id':fld(ID,'Observable tracked scope.'),'successes':fld(integer(),'Число уникальных informative success.'),
        'failures':fld(integer(),'Число unique informative failure.'),'opportunities':fld(integer(),'Все opportunities scope, включая DELEGATE.'),
        'alpha':fld(NUM,'1+successes; numeric equality по I21.'),'beta':fld(NUM,'1+failures; numeric equality по I21.')},'B4 state; не evaluator posterior и не historical self-profile.')
    d['calibration_cell']=obj({'calibration_key':fld(ID,'Private key architecture/family/difficulty/context scope.'),
        'architecture':fld(C('architecture'),'Калибруемая configuration architecture.'),'scope':fld(C('scope'),'Scope измерения.'),
        'band':fld(enum('HIGH','MID'),'Hidden admitted stratum.'),'successes':fld(integer(),'Empirical holdout solo successes.'),
        'n':fld(integer(1),'Число holdout items, successes≤n.'),'dataset_hash':fld(SHA,'Hash independent confirmation manifest.')},'Evaluator-only calibration distribution; не сущность агента.')
    config=obj({
        'benchmark_version':fld({'const':'0.1'},'Версия всех контрактов R1.'),
        'planned_run':fld(enum('SMOKE','PILOT'),'Фиксированная матрица 0.1; B5/C4 не входят.'),
        'configuration_status':fld(enum('TEMPLATE','FROZEN'),'TEMPLATE не допускает model execution.'),
        'model_configuration':fld(obj({
            'model_id':fld(st(),'Реальный model ID перед freeze; TEMPLATE допускает CONFIGURE_BEFORE_RUN.'),
            'model_revision':fld(st(),'Immutable provider revision; отсутствие фиксируется до запуска.'),
            'system_prompt_sha256':fld(SHA,'Хеш общего system prompt.'),
            'architecture_prompt_sha256':fld(obj({k:fld(SHA,'Хеш зафиксированного prompt '+k+'.') for k in ['B0','B1','B2','B3','B4']},'Версии architecture interfaces.'),'Архитектурные prompts.'),
            'action_prompt_sha256':fld(SHA,'Хеш общего solver/action instruction.'),
            'context_policy':fld({'const':'EXPLICIT_STATE_NO_HIDDEN_HISTORY'},'Только явно переданное состояние.'),
            'tool_configuration':fld({'const':'DETERMINISTIC_FAMILY_TOOL_V1'},'Ровно два tools G02/G03, по текущей family.'),
            'temperature':fld({'type':'number','minimum':0,'maximum':2},'Одинаковый sampling parameter всех сопоставимых calls.'),
            'top_p':fld(PROB,'Одинаковый top_p; runtime проверяет совместимость provider.'),
            'sampling_seed_supported':fld(BOOL,'Возможность задать model seed; не обещает детерминизма сервиса.')},'Полная identity экспериментальной конфигурации.'),'Config, не agent-facing state.'),
        'architectures':fld({'const':['B0','B1','B2','B3','B4']},'Фиксированная ordered матрица.'),
        'profile_conditions':fld({'const':['C0','C1','C2','C3']},'Фиксированные условия пилота.'),
        'trajectories_per_cell':fld(integer(2,8),'2 SMOKE, 8 PILOT; conditional ниже.'),
        'main_episodes':fld(integer(8,24),'8 SMOKE, 24 PILOT.'),
        'transfer_episodes':fld(integer(4,8),'4 SMOKE, 8 PILOT.'),
        'master_seed':fld(ID,'Private master seed manifest generation.'),
        'history_window':fld(integer(1,32),'ENGINEERING DEFAULT 10, одинаковый всем architectures.'),
        'calibration_bands':fld(obj({'HIGH':fld(C('interval'),'ENGINEERING DEFAULT [.80,.95].'),
                                    'MID':fld(C('interval'),'ENGINEERING DEFAULT [.55,.70].')},'Band means apply to empirical confirmation; not confidence intervals.'),'Configurable target bands; common difficulty gate обязателен.'),
        'profile_stimulus':fld(obj({'false_low_interval':fld(C('interval'),'ENGINEERING DEFAULT [.25,.40] for C2.'),
                                   'false_high_interval':fld(C('interval'),'ENGINEERING DEFAULT [.80,.95] for C3.'),
                                   'evidence_n':fld(integer(1),'ENGINEERING DEFAULT 20, одинаковый видимый stimulus.'),
                                   'evidence_label':fld({'const':'HISTORICAL_ESTIMATE'},'Одинаковый label C1/C2/C3, не признак ложности.')},'Private randomized stimulus settings.'),'Никогда не отправлять config вместе с profile.'),
        'budgets':fld(obj({
            'prep_output_tokens':fld(integer(1),'ENGINEERING DEFAULT 1024 for B1/B2/B3.'),
            'action_output_tokens':fld(integer(1),'ENGINEERING DEFAULT 1024.'),
            'repair_output_tokens':fld(integer(1),'ENGINEERING DEFAULT 512.'),
            'max_input_tokens':fld(integer(1),'ENGINEERING DEFAULT 16384, overflow fails config.'),
            'max_repairs_per_episode':fld({'const':1},'Общий лимит на episode, не по каждому call.'),
            'max_tools_per_episode':fld({'const':1},'Нельзя покупать дополнительные evidence items.'),
            'max_prep_calls':fld({'const':1},'Нет неограниченного reflexive loop.')},'Compute ceilings, не фактическое равенство расходов.'),'Budget fairness settings.'),
        'timeouts':fld(obj({'model_call_seconds':fld(integer(1),'ENGINEERING DEFAULT 120; accepted model timeout PROTOCOL_FAILURE.'),
                           'tool_seconds':fld(integer(1),'ENGINEERING DEFAULT 30; tool timeout INFRA_FAILURE.')},'Timeouts, не бесплатные retries.'),'Configurable deadlines.'),
        'cost_currency':fld(enum('USD','EUR','RUB','UNSPECIFIED'),'Одна валюта resource ledger; default UNSPECIFIED требует monetary_cost=null.'),
        'policy':fld(obj({
            'solo_threshold':fld(PROB,'ENGINEERING DEFAULT τ=0.80.'),
            'tool_cost_units':fld(NUM,'ENGINEERING DEFAULT 1 за VERIFY/DELEGATE tool.'),
            'tracker_prior_alpha':fld({'type':'number','exclusiveMinimum':0},'ENGINEERING DEFAULT 1.'),
            'tracker_prior_beta':fld({'type':'number','exclusiveMinimum':0},'ENGINEERING DEFAULT 1.'),
            'tracker_refresh':fld(integer(1),'ENGINEERING DEFAULT каждая третья opportunity.'),
            'tracker_min_informative':fld(integer(1),'ENGINEERING DEFAULT 4 before confident delegation.'),
            'tracker_uncertain_mass_low':fld(PROB,'ENGINEERING DEFAULT .10.'),
            'tracker_uncertain_mass_high':fld(PROB,'ENGINEERING DEFAULT .90.'),
            'probe_expiry_episodes':fld(integer(1),'ENGINEERING DEFAULT 4.'),
            'restart_new_observations':fld(integer(1),'ENGINEERING DEFAULT 2.'),
            'restart_low_midpoint':fld(PROB,'ENGINEERING DEFAULT 0.40; public restart, не E criterion.'),
            'restart_high_midpoint':fld(PROB,'ENGINEERING DEFAULT 0.80; public restart.')},'Политика действий/stop, не единый reward.'),'Configurable policy defaults.'),
        'evaluator':fld(obj({
            'min_informative':fld(integer(1),'ENGINEERING DEFAULT 4, hidden от агента.'),
            'wrong_band_probability':fld(PROB,'ENGINEERING DEFAULT 0.90 strict greater-than.'),
            'prior_alpha':fld({'type':'number','exclusiveMinimum':0},'ENGINEERING DEFAULT 1.'),
            'prior_beta':fld({'type':'number','exclusiveMinimum':0},'ENGINEERING DEFAULT 1.'),
            'behavioral_margin':fld(PROB,'ENGINEERING DEFAULT δ=0.05.'),
            'resource_margin':fld(NUM,'ENGINEERING DEFAULT 0.20 относительного роста.'),
            'grace_target_opportunities':fld(integer(),'ENGINEERING DEFAULT 2.'),
            'bootstrap_draws':fld(integer(1),'ENGINEERING DEFAULT 10000 trajectory-block samples.')},'Hidden analysis configuration, никогда не agent payload.'),'Evaluator-only settings.'),
        'analysis_windows':fld(obj({'pre_update_opportunities':fld(integer(2,12),'ENGINEERING DEFAULT 4.'),
                                    'post_update_opportunities':fld(integer(2,12),'ENGINEERING DEFAULT 4.'),
                                    'min_each_side':fld(integer(1,12),'ENGINEERING DEFAULT 2, не больше заданных окон.'),
                                    'min_paired_trajectories':fld(integer(1,8),'ENGINEERING DEFAULT 6 для primary classification.'),
                                    'interval_mass':fld(PROB,'ENGINEERING DEFAULT .95 bootstrap/calibration uncertainty interval.')},'Configurable analysis windows; фиксированные ITT adaptation phases не меняются.'),'Анализ не подбирается после observed result.'),
        'calibration_plan':fld(obj({
            'search_n':fld(integer(1),'ENGINEERING DEFAULT 40 per candidate.'),
            'confirm_n':fld(integer(1),'ENGINEERING DEFAULT 200 independent holdout.'),
            'max_interval_width':fld(PROB,'ENGINEERING DEFAULT 0.16 at 95%.'),
            'difficulty_contract_version':fld({'const':'G02_G03_0.1'},'Полные grid/order/validity параметры в generator contract.')},'Не содержит якобы измеренных результатов.'),'Calibration preflight plan.'),
        'generator_options':fld(obj({'max_attempts':fld(integer(1),'ENGINEERING DEFAULT 1000 per item.'),
            'symbolic_sizes':fld(arr(integer(2,8),1,7,True),'ENGINEERING DEFAULT [3,4,6].'),
            'symbolic_lengths':fld(arr(integer(1,40),1,40,True),'ENGINEERING DEFAULT [4,8,12,20,32].'),
            'operation_weights':fld(obj({x:fld(integer(1),'Positive integer generation weight; default1.') for x in ['ADD','MULTIPLY','SWAP','ROTATE','MOD']},'F1 generation weights.'),'Positive operation weights.'),
            'max_abs_intermediate':fld(integer(1,1000000),'ENGINEERING DEFAULT 1000000; no overflow wrap.'),
            'grid_sizes':fld(arr(integer(2,5),1,4,True),'ENGINEERING DEFAULT [3,4,5].'),
            'grid_properties':fld(arr(integer(1,3),1,3,True),'ENGINEERING DEFAULT [1,2,3].'),
            'max_grid_assignments':fld(integer(1),'ENGINEERING DEFAULT 2000000.'),
            'constraint_weights':fld(obj({x:fld(integer(1),'Positive integer generation weight.') for x in ['EQ','NEQ','IMPLIES','XOR']},'Defaults1,2,2,2 respectively.'),'F2 weights; parameter sampling remains G03.'),
            'min_clue_factor':fld(integer(1),'Default1: minimum n * factor.'),
            'max_clue_factor':fld(integer(1,4),'Default4: maximum n*k*factor, also schema cap60.')},'Configurable search knobs; DSL bounds/op semantics are versioned, not arbitrary runtime knobs.'),'Generator design settings; no generated tasks.')},'Private R1 experiment config.')
    config['allOf']=[{'if':{'properties':{'planned_run':{'const':mode}}},'then':{'properties':{
        'trajectories_per_cell':{'const':n},'main_episodes':{'const':m},'transfer_episodes':{'const':t}}}} for mode,n,m,t in [('SMOKE',2,8,4),('PILOT',8,24,8)]]
    config['$defs']=d

    claim=obj({'claim_id':fld(ID,'Stable slot identity, без target/control marker.'),
        **{k:copy.deepcopy(v) for k,v in d['scope']['properties'].items()},
        'estimated_success_interval':fld(nullable(C('interval')),'Probability claim; null iff UNKNOWN.'),
        'evidence_label':fld(enum('HISTORICAL_ESTIMATE','OBSERVED_OUTCOMES'),'Происхождение stimulus либо accepted local data.'),
        'evidence_n':fld(integer(),'Initial stimulus=20; subsequent count derived from refs, не confidence.'),
        'status':fld(C('claim_status'),'Единый claim lifecycle §10.'),
        'version':fld(integer(1),'Claim version, возрастает на каждую recorded status stage.'),
        'last_updated_episode':fld(integer(),'0 initial; effective episode последнего commit.')},'Current scoped capability claim.')
    claim['allOf']=[{'if':{'properties':{'status':{'const':'UNKNOWN'}}},'then':{'properties':{'estimated_success_interval':{'type':'null'}}},
        'else':{'properties':{'estimated_success_interval':C('interval')}}}]
    proposal=obj({'proposal_id':fld(ID,'Immutable ID proposal.'),'claim_id':fld(ID,'Существующий slot, не новый global trait.'),
        'expected_version':fld(integer(1),'Optimistic concurrency version before commit.'),
        'new_status':fld(C('claim_status'),'Requested terminal status; stages derived from lifecycle.'),
        'new_interval':fld(nullable(C('interval')),'Предлагаемая оценка, null для UNKNOWN.'),
        'new_scope':fld(C('scope'),'Явный proposed scope; сравнить с existing, не judge prose.'),
        'evidence_refs':fld(arr(ID,0,32,True),'Known past feedback episode IDs; admissibility I05/I21.'),
        'restore_version':fld(nullable(integer(1)),'Точный historical version для rollback; иначе null.'),
        'basis':fld(st(240),'Краткое operational основание, не chain-of-thought.')},'Общий B2/B3 proposal adapter; не подтверждение истинности.')
    update=obj({'proposal':fld(P('proposal'),'Исходное proposal без переписывания evaluator.'),
        'validation_status':fld(enum('COMMITTED','REJECTED'),'Проверка допустимости/authority, не empirical verification.'),
        'rejection_codes':fld(arr(enum('STALE_VERSION','UNKNOWN_CLAIM','FUTURE_EVIDENCE','NO_LOCAL_EVIDENCE','SCOPE_VIOLATION','LIFECYCLE_VIOLATION','INVALID_INTERVAL','UNAUTHORIZED_ACTOR'),0,8,True),'Пусто у COMMITTED.'),
        'transition_path':fld(arr(C('claim_status'),0,3),'Последовательность включая before; 2–3 у COMMITTED, [] у REJECTED.'),
        'before_claim':fld(nullable(P('claim')),'Snapshot перед попыткой; null если rejected UNKNOWN_CLAIM.'),'after_claim':fld(nullable(P('claim')),'Snapshot после commit, null у rejected.'),
        'effective_episode':fld(integer(1),'Изменение активно для ACTION именно этого episode.')},'Append-only profile history event; empirical verdict хранится отдельно evaluator.')
    update['allOf']=[{'if':{'properties':{'validation_status':{'const':'COMMITTED'}}},'then':{'properties':{
        'before_claim':P('claim'),'after_claim':P('claim'),'transition_path':{'minItems':2},'rejection_codes':{'maxItems':0}}},'else':{'properties':{
        'after_claim':{'type':'null'},'transition_path':{'maxItems':0},'rejection_codes':{'minItems':1}}}}]
    profile=obj({'profile_id':fld(ID,'Opaque self-profile ID.'),'version':fld(integer(1),'Profile snapshot version; +1 на атомарный accepted proposal.'),
        'claims':fld(arr(P('claim'),2,2),'Два capability slots в profile-present trajectory.')},'Текущий self-profile; для C0/B4 весь объект null.')
    profile['$defs']={'claim':claim,'proposal':proposal,'update_event':update}

    def prep(kind,props):return obj({'record_kind':fld({'const':kind},'Architecture-specific decision interface, не hidden condition.'),**props},'Observable PREP record, не chain-of-thought.')
    memo={'memo':fld(st(480),'Краткий actionable memo, без приватного рассуждения.'),
          'recommended_action':fld(C('action'),'Рекомендация не считается фактическим action.'),'confidence':fld(C('confidence'),'Категориальный report.')}
    b1=prep('EXTRA_COMPUTE',memo)
    b2=prep('GENERIC_CRITIC',{**memo,'proposal':fld(nullable(P('proposal')),'Общий update adapter; null если не предлагается.')})
    b3=prep('MATRYOSHKA_REFLEXIVE',{
        'relevant_self_claim':fld(nullable(ID),'Адрес claim; null у C0 или без relevant claim.'),
        'observed_mismatch':fld(obj({'evidence_refs':fld(arr(ID,0,10,True),'Референсы past observable feedback.'),
            'description':fld(st(240),'Краткое различие; NONE допустим как literal description.')},'Decision interface, не механизм.'),'Наблюдаемое несовпадение.'),
        'candidate_loci':fld(arr(C('locus'),1,5,True),'Альтернативные адреса объяснения, не установленная cause.'),
        'probe_needed':fld(BOOL,'Заявленная потребность, не факт исполнения.'),'probe_type':fld(C('probe_type'),'Тип bounded probe §9.'),
        'probe_predictions':fld(arr(C('probe_prediction'),0,5),'До действия зафиксированные predictions; [] при NONE.'),
        'profile_update_status':fld(enum('NO_CHANGE','ACTIVE','QUESTIONED','REVISED','NARROWED','UNKNOWN'),'Requested status, не validated commit.'),
        'proposed_new_interval':fld(nullable(C('interval')),'Зеркало proposal.new_interval; null при NO_CHANGE/UNKNOWN.'),
        'proposed_new_scope':fld(nullable(C('scope')),'Зеркало proposal.new_scope; null при NO_CHANGE.'),
        'action':fld(C('action'),'PREP action suggestion, ACTION output отдельно.'),
        'confidence':fld(C('confidence'),'Не primary numerical confidence.'),'stop_reflection':fld(BOOL,'Закрывает reflexive chain, не action.'),
        'proposal':fld(nullable(P('proposal')),'Единственный источник update для commit; зеркала должны совпадать.')})
    b3['allOf']=[{'if':{'properties':{'probe_needed':{'const':True}}},'then':{'properties':{
        'probe_type':{'not':{'const':'NONE'}},'candidate_loci':{'minItems':2},'probe_predictions':{'minItems':2}}},'else':{'properties':{'probe_type':{'const':'NONE'},'probe_predictions':{'maxItems':0}}}},
        {'if':{'properties':{'profile_update_status':{'const':'NO_CHANGE'}}},'then':{'properties':{
            'proposal':{'type':'null'},'proposed_new_interval':{'type':'null'},'proposed_new_scope':{'type':'null'}}},
         'else':{'properties':{'proposal':P('proposal'),'proposed_new_scope':C('scope')}}}]
    reflex={'oneOf':[R('b1'),R('b2'),R('b3')],'$defs':{'b1':b1,'b2':b2,'b3':b3},'description':'PREP interfaces; B2 is not given B3 schema/vocabulary.'}

    feedback=obj({'episode_id':fld(ID,'Opaque завершённый episode.'),'task_family':fld(C('family'),'Family наблюдения.'),
        'scope_id':fld(ID,'Стабильный capability scope наблюдения.'),
        'difficulty_scope':fld(ID,'Observable difficulty ID текущего item; нужен для subset evidence.'),
        'context_condition':fld(ID,'Observable context ID текущего item; не hidden calibration band.'),
        'chosen_action':fld(nullable(C('action')),'null если не получен valid action.'),
        'solo_correct':fld(nullable(BOOL),'true/false только наблюдаемое SOLO/pre-tool VERIFY; иначе null.'),
        'final_correct':fld(nullable(BOOL),'Exact task correctness; null для no answer.'),'tool_used':fld(BOOL,'Фактически выполнен tool call.'),
        'cost_units':fld(NUM,'Фактические units инструмента, не composite reward.'),
        'outcome':fld(enum('CORRECT','INCORRECT','ABSTAINED','PROTOCOL_FAILURE','INFRA_FAILURE'),'Стандартный исход без hidden cause.')},'Единственная разрешённая feedback projection; correct content не раскрывается автоматически.')
    call=obj({'call_id':fld(ID,'Call event ID.'),'phase':fld(enum('PREP','ACTION','REPAIR'),'Назначение вызова.'),
        'repair_of':fld(nullable(enum('PREP','ACTION')),'Для REPAIR — исходная фаза, иначе null.'),
        'input_sha256':fld(SHA,'Хеш фактически отправленного payload.'),'output_sha256':fld(SHA,'Хеш видимого structured output.'),
        'visible_output':fld({'type':'string','maxLength':20000},'Только final-channel public structured output; hidden reasoning запрещён.'),
        'input_tokens':fld(integer(),'Фактические input tokens.'),'output_tokens':fld(integer(),'Фактические public output tokens.'),
        'reasoning_tokens':fld(nullable(integer()),'Provider usage count либо null, никогда reasoning text.'),
        'cached_tokens':fld(nullable(integer()),'Observed cached count либо null.'),'latency_ms':fld(nullable(NUM),'Измеренная latency либо null.'),
        'monetary_cost':fld(nullable(NUM),'Денежная стоимость в configured currency либо null.'),
        'model_revision':fld(st(),'Observed serving revision.'),'sequence':fld(integer(1),'Monotone event sequence для проверки ordering.')},'Immutable usage/observable output; не hidden chain-of-thought.')
    tool=obj({'tool_name':fld(enum('run_symbolic_pipeline','solve_rule_grid'),'Только tool текущей family.'),
        'input_spec_sha256':fld(SHA,'Должен совпасть с task spec.'),'result':fld(nullable(C('answer')),'Correct canonical output либо null при infra error.'),
        'status':fld(enum('OK','INFRA_FAILURE'),'Tool failure не изменение capability.'),'start_sequence':fld(integer(1),'После solo seal у VERIFY.'),
        'end_sequence':fld(integer(1),'Порядок завершения event.'),'cost_units':fld(NUM,'Фактический tool cost.')},'Tool event; не содержит calibration/condition.')
    probe=obj({'probe_type':fld(C('probe_type'),'Declared probe NONE если не B3/не объявлена.'),
        'predictions':fld(arr(C('probe_prediction'),0,5),'Sealed predictions; copied from B3 declaration, [] для NONE.'),
        'reference_episode':fld(nullable(ID),'Past matching feedback for NEXT_MATCHED comparison; иначе null.'),
        'scope_id':fld(nullable(ID),'Scope intention, null для NONE.'),'declared_episode':fld(nullable(integer(1)),'Начало probe intention.'),
        'expires_episode':fld(nullable(integer(1)),'Expiry NEXT_MATCHED, иначе null.'),'executed':fld(BOOL,'Совпадение фактического action и допустимой probe.'),
        'resolution':fld(enum('NONE','PENDING','EVIDENCE_RETURNED','CANCELLED','EXPIRED'),'Не утверждает причинную идентификацию.')},'Observable probe bookkeeping, не дополнительный task.')
    probe['allOf']=[{'if':{'properties':{'probe_type':{'const':'NONE'}}},'then':{'properties':{
        'predictions':{'maxItems':0},'reference_episode':{'type':'null'},'scope_id':{'type':'null'},'executed':{'const':False}}},
        'else':{'properties':{'predictions':{'minItems':2},'scope_id':ID,'declared_episode':integer(1)}}},
        {'if':{'properties':{'probe_type':{'const':'VERIFY_NEXT_MATCHED'}}},'then':{'properties':{'reference_episode':ID}},
         'else':{'properties':{'reference_episode':{'type':'null'}}}}]
    private=obj({'phase':fld(C('phase'),'Evaluator-only experimental phase.'),'target_role':fld(enum('TARGET','CONTROL'),'Hidden manipulated/control slot role.'),
        'split':fld(C('split'),'Dataset split; never agent payload.'),'latent_fingerprint':fld(SHA,'Split dedup key.'),
        'surface_template_id':fld(ID,'Hidden rendering provenance.'),'calibration_key':fld(ID,'Private calibration reference.'),
        'ground_truth':fld(C('answer'),'Answer secret before tool/feedback.'),
        'sufficient_before':fld(BOOL,'E computed from prior observations, hidden.'),'posterior_wrong_before':fld(nullable(PROB),'q_it, null C0.'),
        'direction_before':fld(enum('UPWARD','DOWNWARD','UNRESOLVED','NOT_APPLICABLE'),'Hidden directional sufficient-evidence conclusion.'),
        'informative':fld(BOOL,'Post-episode admissible unique solo observation according to E01.')},'Private evaluator data; forbidden under every agent-state projection.')
    episode=obj({'benchmark_version':fld({'const':'0.1'},'Record version.'),'trajectory_id':fld(ID,'Opaque trajectory ID.'),
        'episode_id':fld(ID,'Unique opaque episode ID.'),'episode_index':fld(integer(1,32),'1-based within trajectory.'),
        'agent_input':fld(T('agent_state'),'Exact allowlisted state at PREP start.'),
        'action_input_profile':fld(nullable(ref('r1_self_profile')),'Profile after commit actually supplied to ACTION.'),
        'prep_record':fld(nullable(ref('r1_reflexive_record')),'null if not called or invalid after repair.'),
        'action_record':fld(nullable(C('action_record')),'Sealed ACTION output, null on failure.'),
        'solo_seal_sequence':fld(nullable(integer(1)),'Pre-tool event order or null when no solo answer.'),
        'final_answer':fld(nullable(C('answer')),'Final output from action/tool; never retroactive solo answer.'),
        'tool_event':fld(nullable(E('tool_event')),'At most one tool event.'),
        'update_event':fld(nullable(P('update_event')),'Profile update separate from answer; null if none.'),
        'probe_event':fld(E('probe_event'),'Declared vs executed probe.'),'feedback':fld(E('feedback'),'Only public observable feedback.'),
        'calls':fld(arr(E('call_usage'),0,3),'Actual PREP/ACTION/one REPAIR, not hidden provider reasoning.'),
        'protocol_status':fld(enum('OK','PROTOCOL_FAILURE','INFRA_FAILURE'),'Explicit technical outcome class.'),
        'protocol_errors':fld(arr(st(),0,20),'Machine-checkable validation error codes/messages, no hidden truth.'),
        'evaluator_private':fld(E('evaluator_private'),'Never sent to model.')},'Full private log record, not agent-facing payload.')
    episode['$defs']={'feedback':feedback,'call_usage':call,'tool_event':tool,'probe_event':probe,'evaluator_private':private}

    ledger=obj({'scope_id':fld(ID,'Public scope.'),'n':fld(integer(),'Count informative outcomes, successes≤n.'),
        'successes':fld(integer(),'Count observed solo success.')},'Common observable aggregate, same access across B0–B4.')
    stop=obj({'scope_id':fld(nullable(ID),'Latched scope, null global/C0.'),'latched':fld(BOOL,'PREP stopped for this scope.'),
        'since_episode':fld(integer(),'Last latch update; 0 initial.'),'new_observations':fld(integer(),'Count since latch, not evaluator posterior.'),
        'pending_probe':fld(nullable(E('probe_event')),'Only B3-owned pending intention, no private task schedule.')},'B3-only explicit state.')
    agent=obj({'trajectory_id':fld(ID,'Opaque run identity, no cell label.'),'episode_index':fld(integer(1,32),'Current opportunity index.'),
        'task_view':fld(C('task_view'),'Only current task without ground truth.'),'current_profile':fld(nullable(ref('r1_self_profile')),'Visible current profile; null C0/B4.'),
        'profile_history':fld(arr(P('update_event'),0,32),'Latest history_window events; no hidden validation truth.'),
        'recent_episode_history':fld(arr(E('feedback'),0,32),'Latest history_window public feedback rows, no task answers.'),
        'evidence_ledger':fld(arr(T('ledger_entry'),0,20),'All prior observable counts, common to every architecture.'),
        'cumulative_cost':fld(NUM,'Actual total tool cost_units so far, not reward.'),
        'reflection_cost':fld(integer(),'Accumulated PREP public input+output tokens; richer private resource log separate.'),
        'tracker_state':fld(nullable(arr(C('tracker_state'),0,20)),'Only B4 gets its simple empirical tracker; others null.'),
        'reflexive_state':fld(nullable(arr(T('stop_state'),0,20)),'Only B3 gets its own stop/probe latch; others null.')},'Closed agent-facing allowlist. No architecture/profile_condition/seed/evaluator fields permitted.')
    trajectory=obj({'benchmark_version':fld({'const':'0.1'},'R1 version.'),'trajectory_id':fld(ID,'Opaque unique ID.'),
        'config_sha256':fld(SHA,'Frozen complete config identity.'),'architecture':fld(C('architecture'),'Harness-private treatment code.'),
        'profile_condition':fld(C('profile_condition'),'Harness-private condition, never model input.'),
        'planned_run':fld(enum('SMOKE','PILOT'),'Determines schedule counts.'),
        'block_id':fld(ID,'Private matched-block key for paired analysis.'),
        'target_family':fld(C('family'),'Private target assignment.'),'first_family':fld(C('family'),'Private ordering assignment.'),
        'target_stratum':fld(enum('HIGH','MID'),'Private real capability stratum.'),
        'seed_metadata':fld(obj({k:fld(SHA,'Derived private seed digest for '+k+'.') for k in ['TASK','FAMILY_ORDER','SURFACE','PROFILE','MODEL','BOOTSTRAP']},'Domain-separated seeds; never agent payload.'),'Private reproducibility metadata.'),
        'calibration_cells':fld(arr(C('calibration_cell'),2,20),'Read-only empirical reference distributions.'),
        'initial_profile':fld(nullable(ref('r1_self_profile')),'Original stimulus; null B4/C0.'),
        'current_profile':fld(nullable(ref('r1_self_profile')),'Replay-derived current profile.'),
        'profile_history':fld(arr(P('update_event'),0,32),'Full append-only attempts/commit log.'),
        'recent_episode_history':fld(arr(E('feedback'),0,32),'Projection cache, recomputed from records using config history_window.'),
        'cumulative_cost':fld(NUM,'Total tool units, same meaning as agent field.'),
        'reflection_cost':fld(integer(),'Total PREP public input+output tokens.'),
        'episodes':fld(arr(ref('r1_episode_record'),0,32),'Ordered private records; partial during run.'),
        'completion_status':fld(enum('PLANNED','RUNNING','COMPLETED','INFRA_INVALID'),'Not a scientific outcome.'),
        'initial_stimulus_intervals':fld(arr(obj({'scope_id':fld(ID,'Hidden scope mapping.'),
            'interval':fld(nullable(C('interval')),'Original J0, also for B4 matched evaluation; null C0.')},'Frozen evaluator reference.'),2,2),'Kept fixed even after agent profile update.')},'Full harness-private trajectory. MUST NOT be serialized directly as model input.')
    trajectory['allOf']=[{'if':{'anyOf':[{'properties':{'profile_condition':{'const':'C0'}}},{'properties':{'architecture':{'const':'B4'}}}]},
        'then':{'properties':{'initial_profile':{'type':'null'},'current_profile':{'type':'null'},'profile_history':{'maxItems':0}}}}]
    trajectory['$defs']={'agent_state':agent,'ledger_entry':ledger,'stop_state':stop}
    from schema_changes_02 import amend
    return amend(dict(zip(NAMES,[config,profile,episode,reflex,trajectory])))


def main(output=None):
    output=Path(output).resolve() if output else ROOT
    schemas=make()
    directory=output/'schemas';directory.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name,schema in schemas.items():
        schema.update({'$schema':'https://json-schema.org/draft/2020-12/schema','$id':BASE+name+'.schema.json','title':name+' contract 0.2.1'})
        (directory/(name+'.schema.json')).write_bytes((json.dumps(schema,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
        def walk(node,path):
            if isinstance(node,dict):
                for key,value in (node.get('properties',{}) if node.get('type')=='object' else {}).items():
                    if 'description' in value:
                        rows.append((name,path+'/properties/'+key,value['description']))
                for key,value in node.items():walk(value,path+'/'+key)
            elif isinstance(node,list):
                for i,value in enumerate(node):walk(value,path+'/'+str(i))
        walk(schema,'#')
    text='# MRAB-R1 — точный словарь полей\n\nСгенерирован из пяти schemas; schema JSON Pointer — единственный адрес определения. `$ref` переиспользует определение, а не создаёт иной смысл. Межобъектные ограничения I01–I24 заданы в SPEC. Полные private records запрещены в agent payload.\n\n| Schema | JSON Pointer | Значение |\n| --- | --- | --- |\n'
    for name,path,description in sorted(rows):text+=f'| {name} | `{path}` | {description.replace("|","/")} |\n'
    (output/'MRAB_R1_FIELD_DICTIONARY.md').write_bytes(text.encode('utf-8'))
    print(json.dumps({'schemas_written':len(schemas),'field_occurrences_documented':len(rows),'benchmark_runtime_created':False}))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description='Explicit schema builder, never a read-only verifier')
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args().output)
