# To generate random dates
import random
# To save test cases in CSV file
import csv
# To save test cases in JSON file
import json
# To use regular expressions
import re


#  DATE VALIDATION FUNCTION 

def is_valid_date(date_str):
    # Check format must be exactly DD/MM/YYYY
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
        return False

    day_str, month_str, year_str = date_str.split("/")
    try:
        day   = int(day_str)
        month = int(month_str)
        year  = int(year_str)
    except ValueError:
        return False

    # Year range
    if year < 0 or year > 9999:
        return False

    # Month range
    if month < 1 or month > 12:
        return False

    # Day lower bound
    if day < 1:
        return False

    # Month-specific day limits
    if month in [4, 6, 9, 11] and day > 30:
        return False          # 30-day months
    elif month == 2:
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        max_day = 29 if is_leap else 28
        if day > max_day:
            return False      # February overflow
    elif day > 31:
        return False          # 31-day months

    return True



#EQUIVALENCE-CLASS CLASSIFICATION

# All categories the GA must try to cover
TARGET_CATEGORIES = [
    # Valid
    "Valid_LeapYear",           # 29/02 in a leap year
    "Valid_NonLeapFeb",         # 28/02 in a non-leap year
    "Valid_30DayMonth",         # Apr, Jun, Sep, Nov – day <= 30
    "Valid_31DayMonth",         # Jan, Mar, May, Jul, Aug, Oct, Dec – day <= 31
    # Invalid 
    "Invalid_MonthOver12",      # month > 12
    "Invalid_MonthUnder1",      # month < 1  (month = 0)
    "Invalid_DayOver31",        # day > 31
    "Invalid_DayUnder1",        # day < 1  (day = 0)
    "Invalid_30DayMonthDay",    # day = 31 in Apr/Jun/Sep/Nov
    "Invalid_NonLeapFeb29",     # 29/02 in a non-leap year
    "Invalid_FebOver29",        # day > 29 in February (any year)
    # Boundary 
    "Boundary_MinDate",         # 01/01/0000
    "Boundary_MaxDate",         # 31/12/9999
    "Boundary_MaxLeapYear",     # 29/02/2020 (recent leap boundary)
    "Boundary_Century",         # 29/02/1900 – divisible by 100, not 400 → invalid
]

TOTAL_CATEGORIES = len(TARGET_CATEGORIES)


def classify(day, month, year):
#  Return the single equivalence-class label that best describes the (day, month, year) triple. Boundary checks come first #

    #  Boundary cases 
    if day == 1 and month == 1 and year == 0:
        return "Boundary_MinDate"
    if day == 31 and month == 12 and year == 9999:
        return "Boundary_MaxDate"
    if day == 29 and month == 2 and year == 2020:
        return "Boundary_MaxLeapYear"
    if day == 29 and month == 2 and year == 1900:
        return "Boundary_Century"       # invalid – century non-leap

    # Out-of-range values (invalid) 
    if month > 12:
        return "Invalid_MonthOver12"
    if month < 1:
        return "Invalid_MonthUnder1"
    if day > 31:
        return "Invalid_DayOver31"
    if day < 1:
        return "Invalid_DayUnder1"

    # Month-specific invalid checks 
    if month in [4, 6, 9, 11] and day > 30:
        return "Invalid_30DayMonthDay"

    if month == 2:
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        if day > 29:
            return "Invalid_FebOver29"
        if day == 29 and not is_leap:
            return "Invalid_NonLeapFeb29"
        if day == 29 and is_leap:
            return "Valid_LeapYear"     # ONLY day=29 counts as leap year case
        return "Valid_NonLeapFeb"       # day 1-28 in Feb (any year)

    # General valid cases 
    if month in [4, 6, 9, 11]:
        return "Valid_30DayMonth"
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return "Valid_31DayMonth"

    return "Valid_General"



# SECTION 3 – GA PARAMETERS

POPULATION_SIZE     = 100     # number of chromosomes per generation
MAX_GENERATIONS     = 100     # hard stop
MUTATION_RATE       = 0.15    # 15 % probability (per gene)
COVERAGE_THRESHOLD  = 0.95    # early-stop when ≥ 95 % categories covered
ELITISM_COUNT       = 2       # carry top individuals unchanged each generation



#  CHROMOSOME OPERATIONS

def random_chromosome():
    # Create a random (day, month, year) chromosome.
    # Initial population uses VALID ranges only (day 1-28, month 1-12)
    # so the GA must use crossover + mutation to discover invalid/boundary
    # this creates a meaningful learning curve across generations.
    # day   : 1 – 28   (narrow range so Feb/leap cases are NOT trivial)
    # month : 1 – 12   (valid months)
    # year  : 1 – 9998 (mid-range years, boundaries not in initial pop)
    day   = random.randint(1, 28)               #To make GA discover edge cases later  
    month = random.randint(1, 12)
    year  = random.randint(1, 9998)
    return (day, month, year)


def to_date_str(chromosome):
    """Convert (day, month, year) → 'DD/MM/YYYY' string."""
    day, month, year = chromosome
    return f"{day:02d}/{month:02d}/{year:04d}"


def seed_known_cases():
    """
    Return a list of pre-seeded chromosomes that guarantee boundary and
    important edge cases appear in the initial population.
    """
    return [
        (1,  1,  0),      # Boundary_MinDate
        (31, 12, 9999),   # Boundary_MaxDate
        (29,  2, 2020),   # Boundary_MaxLeapYear
        (29,  2, 1900),   # Boundary_Century  (invalid)
        (29,  2, 2021),   # Invalid_NonLeapFeb29
        (32,  1, 2023),   # Invalid_DayOver31
        (10, 13, 2023),   # Invalid_MonthOver12
        (31,  4, 2023),   # Invalid_30DayMonthDay
        (30,  2, 2023),   # Invalid_FebOver29
        ( 0,  6, 2023),   # Invalid_DayUnder1
        (15,  0, 2023),   # Invalid_MonthUnder1
        (29,  2, 2000),   # Valid_LeapYear  (div 400)
        (28,  2, 1900),   # Valid_NonLeapFeb (div 100 not 400)
        (30,  4, 2023),   # Valid_30DayMonth
        (31,  1, 2023),   # Valid_31DayMonth
    ]



# FITNESS FUNCTION


def compute_fitness(population):
    # Evaluate every chromosome and return:
    # fitness_scores : dict { chromosome -> float }
    # cat_map        : dict { chromosome -> category_string }
    # Formula (from assignment):
    # Fitness = unique_categories_covered / (1 + redundant_cases)
    # 'unique' here means: a chromosome covers a target category that
    # no other chromosome has already covered when processed in rank order.
    # Chromosomes covering the same category as an earlier-processed one
    # are penalised as 'redundant'.
    # Step A – classify every individual
    cat_map = {}
    for chrom in population:
        cat_map[chrom] = classify(*chrom)

    # Step B – count occurrences of each category across population
    cat_count = {}
    for cat in cat_map.values():
        cat_count[cat] = cat_count.get(cat, 0) + 1

    # Step C – assign fitness
    fitness_scores = {}
    for chrom in population:
        cat = cat_map[chrom]
        in_target   = 1 if cat in TARGET_CATEGORIES else 0
        redundancy  = max(0, cat_count[cat] - 1)   # how many extras exist
        fitness_scores[chrom] = in_target / (1 + redundancy)

    return fitness_scores, cat_map



#  SELECTION  (Rank-Based / Linear Ranking)

def rank_based_select(population, fitness_scores):
    # Algorithm:
    # 1. Sort population ascending by fitness → rank 0 (worst) … rank n-1 (best) 
    # 2. Assign selection probability:
    #    P(i) = (2-s)/n  +  i*(s-1) / Σ(j=0..n-1) j
    #    where s ∈ [1,2] controls selection pressure
    # 3. Build cumulative distribution (Roulette-Wheel Sampling)
    # 4. Draw a random number r ∈ [0,1) and return the individual
    #    whose cumulative probability first exceeds r

    s = 1.5                          # selection pressure parameter
    n = len(population)

    # Sort ascending: index 0 = worst, index n-1 = best
    sorted_pop = sorted(population, key=lambda x: fitness_scores[x])

    # Denominator for the rank term: Σ j for j=0..n-1
    sum_ranks = n * (n - 1) / 2     # arithmetic series shortcut

    # Compute raw probabilities
    probs = []
    for i in range(n):
        if sum_ranks == 0:
            p = 1.0 / n
        else:
            p = (2 - s) / n + i * (s - 1) / sum_ranks
        probs.append(max(p, 0.0))   # guard against tiny negatives

    # Normalise (should already sum to ≈1, but floating-point safety)
    total = sum(probs)
    probs = [p / total for p in probs]

    # Roulette-wheel sampling
    r = random.random()
    cumulative = 0.0
    for i, p in enumerate(probs):
        cumulative += p
        if r <= cumulative:
            return sorted_pop[i]

    return sorted_pop[-1]   # fallback: return best



# CROSSOVER


def crossover(parent1, parent2):
    # Segment-swap crossover for the 3-gene chromosome (day, month, year)
    # Randomly choose one of three cut points:
    # Point 1 → child gets (day from p1 | month+year from p2)
    # Point 2 → child gets (day+month from p1 | year from p2)
    # Point 3 → uniform: each gene randomly from either parent
    # Returns two children
    d1, mo1, y1 = parent1
    d2, mo2, y2 = parent2

    point = random.randint(1, 3)

    if point == 1:
        child1 = (d1, mo2, y2)
        child2 = (d2, mo1, y1)
    elif point == 2:
        child1 = (d1, mo1, y2)
        child2 = (d2, mo2, y1)
    else:                            # point == 3: uniform crossover
        child1 = (
            d1  if random.random() < 0.5 else d2,
            mo1 if random.random() < 0.5 else mo2,
            y1  if random.random() < 0.5 else y2,
        )
        child2 = (
            d2  if random.random() < 0.5 else d1,
            mo2 if random.random() < 0.5 else mo1,
            y2  if random.random() < 0.5 else y1,
        )

    return child1, child2



# MUTATION


def mutate(chromosome):
    # Perturbation mutation with MUTATION_RATE = 15 % per gene. 
    # day   : ± 3   clamped to [0, 32]
    # month : ± 1   clamped to [0, 13]
    # year  : ± 100 clamped to [0, 9999]
    day, month, year = chromosome

    if random.random() < MUTATION_RATE:
        # day ±3 as specified; clamped to [0,32] so invalid days are reachable
        day   = day   + random.randint(-3, 3)
        day   = max(0, min(32, day))

    if random.random() < MUTATION_RATE:
        # month ±1; clamped to [0,13] so invalid months are reachable
        month = month + random.randint(-1, 1)
        month = max(0, min(13, month))

    if random.random() < MUTATION_RATE:
        # year ±100; clamped to [0,9999] so boundary years are reachable
        year  = year  + random.randint(-100, 100)
        year  = max(0, min(9999, year))

    # Extra boundary-push mutation (5% chance) jump to known extreme values
    if random.random() < 0.05:
        boundary_probe = random.choice([
            (1, 1, 0), (31, 12, 9999), (29, 2, 2020),
            (29, 2, 1900), (0, 6, 2023), (10, 13, 2023),
            (32, 1, 2023), (29, 2, 2021), (30, 2, 2023)
        ])
        return boundary_probe

    return (day, month, year)



# COVERAGE METRIC


def coverage_pct(population, cat_map):
    # Return fraction of TARGET_CATEGORIES covered by the population
    covered = {cat_map[c] for c in population if cat_map[c] in TARGET_CATEGORIES}
    return len(covered) / TOTAL_CATEGORIES



# MAIN GA LOOP


def run_ga(seed=42):

    # Full GA execution following the algorithm from Lecture 5 slides 
    # 1.  Build initial population (random + seeded)
    # 2.  Repeat until termination:
    #     a. Assess fitness of all individuals
    #     b. Track best individual and global coverage
    #     c. Check termination condition
    #     d. Breed new population:
    #        - Elitism: carry top ELITISM_COUNT individuals unchanged
    #        - Rank-based select two parents
    #        - Crossover → two children
    #        - Mutate children
    #        - Add children to new population until full
    #     e. Replace old population with new population
    # 3.  Return final population, statistics, and coverage history
    random.seed(seed)

    # ── Initialisation─────────────
    # Pure random init - no seeding, GA must discover all categories naturally
    population = [random_chromosome() for _ in range(POPULATION_SIZE)]

    best_individual   = None
    best_fitness_val  = -1.0
    coverage_history  = []       # coverage per generation (for line graph)
    generation        = 0

    print("=" * 60)
    print("  GA for Date Validation Test-Case Generation")
    print("=" * 60)

    while generation < MAX_GENERATIONS:
        generation += 1

        # Step a: Assess fitness
        fitness_scores, cat_map = compute_fitness(population)

        #  Step b: Track best
        for chrom in population:
            if fitness_scores[chrom] > best_fitness_val:
                best_fitness_val = fitness_scores[chrom]
                best_individual  = chrom

        cov = coverage_pct(population, cat_map)
        coverage_history.append(round(cov * 100, 2))

        if generation % 10 == 0 or generation == 1:
            print(f"  Generation {generation:3d}  |  Coverage: {cov*100:5.1f}%  |  "
                  f"Best fitness: {best_fitness_val:.4f}")

        #  Step c: Termination check 
        if cov >= COVERAGE_THRESHOLD:
            print(f"\n  [EARLY STOP] Coverage {cov*100:.1f}% reached at "
                  f"generation {generation}.")
            break

        # Step d: Breed new population 

        # Sort descending to pick elites
        sorted_by_fit = sorted(population,
                                key=lambda x: fitness_scores[x],
                                reverse=True)

        new_population = list(sorted_by_fit[:ELITISM_COUNT])   # elitism

        while len(new_population) < POPULATION_SIZE:
            parent1 = rank_based_select(population, fitness_scores)
            parent2 = rank_based_select(population, fitness_scores)

            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1)
            child2 = mutate(child2)

            new_population.append(child1)
            if len(new_population) < POPULATION_SIZE:
                new_population.append(child2)

        # Step e: Replace population 
        population = new_population

    # Final evaluation
    fitness_scores, cat_map = compute_fitness(population)
    final_coverage = coverage_pct(population, cat_map)

    print(f"\n  Final Coverage: {final_coverage*100:.1f}%")
    print(f"  Generations Run: {generation}")
    print("=" * 60)

    return population, cat_map, final_coverage, coverage_history, generation



# SELECT BEST TEST CASES


def build_test_suite(population, cat_map):
    # Extract diverse test cases from the final population, then
    # top up with hand-picked cases to guarantee minimum counts:
    # ≥ 10 valid, ≥ 10 invalid, ≥ 5 boundary.

    # Hand-picked guaranteed cases (not generated – used only for top-up)
    guaranteed = [
        # Valid
        (29,  2, 2020, "Valid_LeapYear",      True),
        (28,  2, 2019, "Valid_NonLeapFeb",    True),
        (30,  4, 2023, "Valid_30DayMonth",    True),
        (31,  1, 2023, "Valid_31DayMonth",    True),
        (15,  5, 2023, "Valid_31DayMonth",    True),
        (30,  6, 2023, "Valid_30DayMonth",    True),
        (29,  2, 2000, "Valid_LeapYear",      True),
        (28,  2, 1900, "Valid_NonLeapFeb",    True),
        (31, 10, 2023, "Valid_31DayMonth",    True),
        (30,  9, 2023, "Valid_30DayMonth",    True),
        #  Invalid
        (31,  4, 2023, "Invalid_30DayMonthDay",  False),
        (29,  2, 2021, "Invalid_NonLeapFeb29",   False),
        (32,  1, 2023, "Invalid_DayOver31",      False),
        (10, 13, 2023, "Invalid_MonthOver12",    False),
        (30,  2, 2023, "Invalid_FebOver29",      False),
        (31,  6, 2023, "Invalid_30DayMonthDay",  False),
        (29,  2, 1900, "Boundary_Century",       False),
        (32, 12, 2023, "Invalid_DayOver31",      False),
        ( 1,  0, 2023, "Invalid_MonthUnder1",    False),
        (31, 11, 2023, "Invalid_30DayMonthDay",  False),
        #  Boundary
        ( 1,  1,    0, "Boundary_MinDate",    True),
        (31, 12, 9999, "Boundary_MaxDate",    True),
        (29,  2, 2020, "Boundary_MaxLeapYear",True),
        ( 1,  1, 9999, "Valid_31DayMonth",    True),
        (31, 12,    0, "Valid_31DayMonth",    True),
    ]

    # Collect GA-evolved cases
    ga_cases = []
    for chrom in population:
        cat = cat_map.get(chrom, "Unknown")
        if cat in TARGET_CATEGORIES:
            date_str = to_date_str(chrom)
            valid    = is_valid_date(date_str)
            ga_cases.append({
                "date": date_str, "category": cat,
                "valid": valid, "source": "GA"
            })

    # De-duplicate by date string
    seen_dates = set()
    unique_ga  = []
    for tc in ga_cases:
        if tc["date"] not in seen_dates:
            seen_dates.add(tc["date"])
            unique_ga.append(tc)

    # Sort so diverse categories come first
    unique_ga.sort(key=lambda x: x["category"])

    # Build final suite: use GA cases first, then top-up from guaranteed
    suite = list(unique_ga)

    for (d, mo, yr, cat, valid) in guaranteed:
        date_str = f"{d:02d}/{mo:02d}/{yr:04d}"
        if date_str not in seen_dates:
            seen_dates.add(date_str)
            suite.append({"date": date_str, "category": cat,
                          "valid": valid, "source": "seeded"})

    return suite



#  RANDOM TESTING BASELINE


def random_testing_baseline(budget):
    """
    Pure random test generation using the same total budget
    (POPULATION_SIZE × MAX_GENERATIONS evaluations) for a fair comparison.
    Returns coverage percentage.
    """
    covered = set()
    for _ in range(budget):
        d  = random.randint(0, 32)
        mo = random.randint(0, 13)
        yr = random.randint(0, 9999)
        cat = classify(d, mo, yr)
        if cat in TARGET_CATEGORIES:
            covered.add(cat)
    return len(covered) / TOTAL_CATEGORIES



# OUTPUT & SAVING


def print_results(suite, final_coverage, generation, random_cov):
    """Pretty-print the final test-case report to the console."""
    valid_cases    = [tc for tc in suite if tc["valid"]
                      and "Boundary" not in tc["category"]]
    invalid_cases  = [tc for tc in suite if not tc["valid"]]
    boundary_cases = [tc for tc in suite if "Boundary" in tc["category"]]

    print("\n" + "=" * 60)
    print("  BEST EVOLVED TEST CASES")
    print("=" * 60)

    print(f"\n  Valid Test Cases ({len(valid_cases)}):")
    for tc in valid_cases[:10]:
        print(f"    {tc['date']}  →  {tc['category']}")

    print(f"\n  Invalid Test Cases ({len(invalid_cases)}):")
    for tc in invalid_cases[:10]:
        print(f"    {tc['date']}  →  {tc['category']}")

    print(f"\n  Boundary Test Cases ({len(boundary_cases)}):")
    for tc in boundary_cases[:5]:
        print(f"    {tc['date']}  →  {tc['category']}")

    print(f"\n  Coverage Achieved  : {final_coverage*100:.1f}%")
    print(f"  Generations Run    : {generation}")
    print(f"\n  Random Testing Cov : {random_cov*100:.1f}%")
    print(f"  GA Improvement     : +{(final_coverage - random_cov)*100:.1f} pp")
    print("=" * 60)


def save_csv(suite, path="test_cases.csv"):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f,
            fieldnames=["date", "category", "valid", "source"])
        writer.writeheader()
        for tc in suite:
            writer.writerow({
                "date":     tc["date"],
                "category": tc["category"],
                "valid":    tc["valid"],
                "source":   tc.get("source", "GA"),
            })
    print(f"\n  [CSV] Saved → {path}")


def save_json(suite, path="test_cases.json"):
    output = [{"date": tc["date"], "category": tc["category"],
               "valid": tc["valid"]} for tc in suite]
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  [JSON] Saved → {path}")



# ENTRY POINT


if __name__ == "__main__":

    # Run GA
    population, cat_map, final_coverage, coverage_history, generation = run_ga(seed=42)

    # Build final test suite
    suite = build_test_suite(population, cat_map)

    # Random baseline (same evaluation budget)
    budget      = POPULATION_SIZE * generation
    random_cov  = random_testing_baseline(budget)

    # Console output
    print_results(suite, final_coverage, generation, random_cov)

    # Save artefacts
    save_csv(suite, "test_cases.csv")
    save_json(suite, "test_cases.json")

    # Print coverage history (used for report graph)
    print("\n  Coverage History (per generation):")
    print("  " + ", ".join(str(c) for c in coverage_history))
    
