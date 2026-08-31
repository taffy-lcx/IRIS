# Taxonomy of Linguistic Realizations Across the IRIS Dimensions

Based on the thematic analysis of 361 sampled security review comments, we construct a taxonomy to characterize how reviewers express the four IRIS dimensions in practice. The taxonomy shows that each dimension is not conveyed in a single uniform manner, but through multiple recurring linguistic strategies that vary in explicitness, depth, and prescriptiveness.

---

## 1. Identification Taxonomy

The **Identification** dimension captures how reviewers signal that a patch contains a defect. We identify six recurrent categories:

- **I1. Defect Diagnosis** 
  The reviewer explicitly names the defect type or gives a high-level diagnosis of the issue.

- **I2. Triggering Scenario Description** 
  The reviewer reveals the defect by describing the execution condition, triggering context, or control-flow scenario under which it occurs.

- **I3. Failure Manifestation** 
  The reviewer identifies the issue indirectly by describing its visible manifestation, such as panic, failure, or attackability.

- **I4. External Evidence** 
  The reviewer grounds the defect identification in tool warnings, static analysis reports, or other external technical evidence.

- **I5. Uncertainty Questioning** 
  The reviewer raises the defect in an interrogative or tentative form, prompting the author to verify the potential flaw.

- **I6. Fix-Implied** 
  The reviewer does not explicitly state the defect, but proposes a remediation from which the underlying issue can be inferred.

---

## 2. Reason Taxonomy

The **Reason** dimension captures how reviewers explain why the identified issue constitutes a real problem. We summarize this dimension into five categories:

- **R1. Rule or Principle** 
  The reviewer justifies the concern by referring to underlying mechanisms, language semantics, or general technical principles.

- **R2. Local Causal Attribution** 
  The reviewer attributes the issue to an immediate local cause, such as a missing check, null value, or unsafe code element.

- **R3. Causal Chain in Execution Flow** 
  The reviewer explains the issue through a multi-step dynamic narrative, tracing how the defect emerges during execution.

- **R4. Best-Practice Reference** 
  The reviewer supports the concern by citing common coding conventions or established engineering best practices.

- **R5. Missing Explicit Reason** 
  The reviewer points out a defect but does not explicitly explain why it occurs.

---

## 3. Impact Taxonomy

The **Impact** dimension characterizes the potential negative outcomes if the defect is left unresolved. We identify six categories:

- **IM1. Runtime Failure** 
  The reviewer warns of immediate execution failures, such as crashes, panics, or exceptions.

- **IM2. Incorrect State and Data Corruption** 
  The reviewer highlights that the defect may produce incorrect program states, corrupted data, or wrong outputs without immediate termination.

- **IM3. Resource and Performance Degradation** 
  The reviewer describes consequences such as memory leaks, resource waste, hangs, or performance deterioration.

- **IM4. Security Exposure** 
  The reviewer frames the consequence as a broader security risk, such as information leakage, unauthorized access, or attacker exploitation.

- **IM5. Unspecified Risk** 
  The reviewer characterizes the code as unsafe, dangerous, or problematic, but without specifying a concrete failure mode.

- **IM6. Missing Explicit Impact** 
  The reviewer does not explicitly state any consequence or negative outcome.

---

## 4. Solution Taxonomy

The **Solution** dimension captures how reviewers communicate remediation guidance and how actionable that guidance is. We identify five categories:

- **S1. Provide a Code Patch** 
  The reviewer supplies a syntactically complete code snippet that directly implements the proposed fix.

- **S2. Documentation Support** 
  The reviewer guides the response by adding or revising source comments or documentation, clarifying specifications, contracts, or terminology, or pointing to authoritative documentation, a reference implementation, or an established example.

- **S3. Strategic Direction** 
  The reviewer suggests a high-level repair direction or mitigation strategy, while leaving the implementation details to the author.

- **S4. Operational Repair** 
  The reviewer provides a detailed and operational natural-language remediation plan, specifying what should be changed and how.

- **S5. Missing Solution** 
  The reviewer identifies the problem but gives no explicit remediation guidance.

---

## Decision Order for Taxonomy Labeling

To ensure consistent annotation, we apply a strict decision order when assigning taxonomy labels within each IRIS dimension. Each comment is mapped to the **first matching category** according to the following rules.

### Identification decision order 

1. If **any external tool evidence, link, rule ID, or report marker** appears, assign **I4. External Evidence**.
2. Else, if the comment is phrased as an **uncertain question or tentative check**, assign **I5. Uncertainty Questioning**.
3. Else, if the comment mainly provides a **fix suggestion while leaving the defect itself implicit**, assign **I6. Fix-Implied**.
4. Else, if the comment mainly describes the **consequence or manifestation** of the issue, assign **I3. Failure Manifestation**.
5. Else, if the comment mainly gives only a **high-level defect name or summary diagnosis**, assign **I1. Defect Diagnosis**.
6. Else, if the comment describes a **triggering scenario, condition, or interleaving**, assign **I2. Triggering Scenario Description**.

### Reason decision order 

1. If the comment explains a **general principle, mechanism, or semantic rule**, assign **R1. Rule or Principle**.
2. Else, if the comment mainly justifies the concern through **best practice, convention, or recommendation**, assign **R4. Best-Practice Reference**.
3. Else, if the comment describes an **execution-flow narrative or multi-step causal chain**, assign **R3. Causal Chain in Execution Flow**.
4. Else, if the comment points to a **specific state, field, nullability issue, or local code element as the direct cause**, assign **R2. Local Causal Attribution**.
5. Else, assign **R5. Missing Explicit Reason**.

### Impact decision order 

1. If the comment analyzes the impact from a **system-security perspective**, such as security exposure, abuse, leakage, bypass, or exploitability, assign **IM4. Security Exposure**.
2. Else, if the comment states a **concrete runtime or program consequence**, then:
   - assign **IM1. Runtime Failure** for crash, panic, or null-dereference style failures;
   - assign **IM2. Incorrect State and Data Corruption** for incorrect state, wrong output, corruption, or overflow;
   - assign **IM3. Resource and Performance Degradation** for out-of-memory, hang, timeout, or throughput/resource degradation.
3. Else, if the comment provides only **unspecified risk wording**, such as race, unsafe, dangerous, or problematic, without a concrete failure mode, assign **IM5. Unspecified Risk**.
4. Else, assign **IM6. Missing Explicit Impact**.

### Solution decision order 

1. If the primary guidance is to **add or revise comments or documentation, clarify a specification, contract, or terminology, or follow an authoritative document, reference implementation, or established example**, assign **S2. Documentation Support**. This rule takes precedence even when the reviewer supplies a complete documentation-comment snippet.
2. Else, if the comment provides a **syntactically complete code block or patch snippet that directly implements the program repair**, assign **S1. Provide a Code Patch**.
3. Else, if the comment gives both a **concrete action** and a **specific target object or location**, assign **S4. Operational Repair**.
4. Else, if the comment shows **solution intent** but leaves the concrete implementation to the author, assign **S3. Strategic Direction**.
5. Else, assign **S5. Missing Solution**.
