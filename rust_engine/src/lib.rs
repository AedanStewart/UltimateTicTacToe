extern crate pyo3;

use pyo3::prelude::*;
use std::collections::HashMap;
use std::vec::Vec;

const WIN_PATTERNS: [u16; 8] = [
    0b111000000,
    0b000111000,
    0b000000111,
    0b100100100,
    0b010010010,
    0b001001001,
    0b100010001,
    0b001010100,
];

const SUBBOARD_WIN_WEIGHT: i64 = 100;
const SUBBOARD_NEAR_WIN_WEIGHT: i64 = 5;
const OVERALL_NEAR_WIN_WEIGHT: i64 = 200;
const REALLY_BIG_NUMBER: i64 = 100_000_000_000;

fn get_subboard(board: (u128, u128, u16, u16), subboard: u16) -> (u16, u16) {
    (
        (board.0 >> (81 - ((subboard + 1) * 9))) as u16 & ((1 << 9) - 1),
        (board.1 >> (81 - ((subboard + 1) * 9))) as u16 & ((1 << 9) - 1),
    )
}

fn make_move(board: (u128, u128, u16, u16), mv: u128, token: i16) -> (u128, u128, u16, u16) {
    let idx: u16 = 80 - mv.trailing_zeros() as u16;
    let subboard_idx: u16 = idx / 9;
    let (mut x_board, mut o_board, mut x_subboards, mut o_subboards) = board;

    if token == 1 {
        x_board = x_board | mv;
        let subboard: (u16, u16) =
            get_subboard((x_board, o_board, x_subboards, o_subboards), subboard_idx);
        if subboard_has_win(subboard.0) {
            x_subboards |= 1 << (8 - subboard_idx)
        }
        return (x_board, o_board, x_subboards, o_subboards);
    } else {
        o_board = o_board | mv;
        let subboard: (u16, u16) =
            get_subboard((x_board, o_board, x_subboards, o_subboards), subboard_idx);
        if subboard_has_win(subboard.1) {
            o_subboards |= 1 << (8 - subboard_idx)
        }
        return (x_board, o_board, x_subboards, o_subboards);
    }
}

fn find_moves(board: (u128, u128, u16, u16), subboard: u16) -> u128 {
    let mut bitmask: u128 = 0;
    let won_boards: u16 = board.2 | board.3;
    let sb: (u16, u16) = get_subboard(board, subboard);
    if (1 << (8 - subboard)) & won_boards != 0 || (sb.0 | sb.1) == ((1 << 9) - 1) {
        for i in 0..9 {
            if won_boards & (1 << i) != 0 {
                bitmask |= ((1 << 9) - 1) << (i * 9);
            }
        }
    } else {
        for i in 0..9 {
            if i != (8 - subboard) {
                bitmask |= ((1 << 9) - 1) << (i * 9);
            }
        }
    }
    ((1 << 81) - 1) ^ (board.0 | board.1 | bitmask)
}

fn subboard_has_win(subboard: u16) -> bool {
    for &pattern in WIN_PATTERNS.iter() {
        if (subboard & pattern) == pattern {
            return true;
        }
    }
    false
}

fn check_win(board: (u128, u128, u16, u16)) -> i16 {
    if subboard_has_win(board.2) {
        return 1;
    }
    if subboard_has_win(board.3) {
        return -1;
    }
    0
}

fn check_draw(board: (u128, u128, u16, u16)) -> bool {
    let overallwins: u16 = board.2 | board.3;
    if overallwins == 0b111111111 {
        return true;
    }
    for i in 0..9 {
        if overallwins & (1 << (8 - i)) != 0 {
            continue;
        }
        let subboard: (u16, u16) = get_subboard(board, i);
        if subboard.0 | subboard.1 != 0b111111111 {
            return false;
        }
    }
    true
}

fn score_subboard(subboard: u16, opponent_subboard: u16) -> i64 {
    let mut score: i64 = 0;
    for &pattern in WIN_PATTERNS.iter() {
        let x_score: i64 = (subboard & pattern).count_ones() as i64;
        let o_score: i64 = (opponent_subboard & pattern).count_ones() as i64;
        if x_score == 2 && o_score == 0 {
            score += 1;
        } else if o_score == 2 && x_score == 0 {
            score -= 1;
        }
    }
    score
}

fn evaluate_board(board: (u128, u128, u16, u16), token: i16) -> i64 {
    let mut evaluation: i64 = 0;

    let cw: i16 = check_win(board);
    if cw != 0 {
        return (cw * token) as i64 * 100_000_000;
    }

    evaluation += board.2.count_ones() as i64 * SUBBOARD_WIN_WEIGHT;
    evaluation -= board.3.count_ones() as i64 * SUBBOARD_WIN_WEIGHT;

    for i in 0..9 {
        let (x_sb, o_sb) = get_subboard(board, i);
        evaluation += score_subboard(x_sb, o_sb) * SUBBOARD_NEAR_WIN_WEIGHT;
    }

    evaluation += score_subboard(board.2, board.3) as i64 * OVERALL_NEAR_WIN_WEIGHT;

    evaluation * token as i64
}

fn order_moves(
    board: (u128, u128, u16, u16),
    moves: u128,
    token: i16,
    cache: &HashMap<(u128, u128, u16, u16), (i16, i64, u16)>,
) -> Vec<u128> {
    let mut move_list_init: Vec<(i64, u128)> = Vec::new();
    let mut all_moves: u128 = moves;

    while all_moves != 0 {
        let mv: u128 = !(all_moves - 1) & all_moves;
        all_moves ^= mv;
        let tentative_board: (u128, u128, u16, u16) = make_move(board, mv, token);

        if cache.contains_key(&tentative_board) {
            move_list_init.push((-cache.get(&tentative_board).unwrap().1, mv));
            continue;
        }

        let subboard: (u16, u16) =
            get_subboard(tentative_board, (80 - mv.trailing_zeros() as u16) % 9);
        let value: i64 = score_subboard(subboard.0, subboard.1) * token as i64;
        move_list_init.push((value, mv));
    }

    let mut move_list: Vec<u128> = Vec::new();
    move_list_init.sort_unstable_by(|a, b| b.0.cmp(&a.0));
    for mv in move_list_init {
        move_list.push(mv.1);
    }
    move_list
}

fn negascout(
    board: (u128, u128, u16, u16),
    subboard: u16,
    token: i16,
    depth: i16,
    cache: &mut HashMap<(u128, u128, u16, u16), (i16, i64, u16)>,
    alpha: i64,
    beta: i64,
) -> (i64, u16) {
    if cache.contains_key(&board) {
        let (ttdepth, ttvalue, ttbestmove) = cache.get(&board).unwrap();
        if ttdepth >= &depth {
            return (*ttvalue, *ttbestmove);
        }
    }

    if depth <= 0 || check_win(board) != 0 || check_draw(board) {
        let evaluation: i64 = evaluate_board(board, token);
        cache.insert(board, (depth, evaluation, 0));
        return (evaluation, 0);
    }

    let all_moves: u128 = find_moves(board, subboard);
    let move_list: Vec<u128> = order_moves(board, all_moves, token, &cache);

    let mut value: i64 = -REALLY_BIG_NUMBER;
    let mut best_move: u16 = 0;
    let mut alp: i64 = alpha;

    for (i, mv) in move_list.iter().enumerate() {
        let mut recur_score: i64;
        if i == 0 {
            recur_score = negascout(
                make_move(board, *mv, token),
                (80 - mv.trailing_zeros() as u16) % 9,
                -token,
                depth - 1,
                cache,
                -beta,
                -alp,
            )
            .0;
        } else {
            recur_score = negascout(
                make_move(board, *mv, token),
                (80 - mv.trailing_zeros() as u16) % 9,
                -token,
                depth - 1,
                cache,
                -alp - 1,
                -alp,
            )
            .0;
            if alpha < -recur_score && -recur_score < beta {
                recur_score = negascout(
                    make_move(board, *mv, token),
                    (80 - mv.trailing_zeros() as u16) % 9,
                    -token,
                    depth - 1,
                    cache,
                    -beta,
                    -alp,
                )
                .0;
            }
        }

        if -recur_score > value {
            value = -recur_score;
            best_move = 80 - mv.trailing_zeros() as u16;
        }
        if value > alp {
            alp = value;
        }
        if alp >= beta {
            break;
        }
    }

    cache.insert(board, (depth, value, best_move));
    (value, best_move)
}

fn iterative_deepening(
    initial_board: (u128, u128, u16, u16),
    subboard: u16,
    token: i16,
    max_depth: i16,
) -> u16 {
    let mut cache: HashMap<(u128, u128, u16, u16), (i16, i64, u16)> = HashMap::new();
    let mut bestmove: u16 = 0;

    for depth in 1..max_depth + 1 {
        bestmove = negascout(
            initial_board,
            subboard,
            token,
            depth,
            &mut cache,
            -REALLY_BIG_NUMBER,
            REALLY_BIG_NUMBER,
        )
        .1;
    }

    bestmove
}

#[pyfunction]
fn find_best_move(
    board: (u128, u128, u16, u16),
    subboard: u16,
    token: i16,
    depth: i16,
) -> PyResult<u16> {
    Ok(iterative_deepening(board, subboard, token, depth))
}

#[pymodule]
fn rust_engine(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_best_move, m)?)?;
    Ok(())
}
