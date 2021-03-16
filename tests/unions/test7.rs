// Unsafe Union field call as parameter to instantiation

fn main() {

	union Sample {
		first: u8,
		second: u8
	}

	struct Example {
		uno: Sample
	}




	let r = Sample{ first: 10 };

	let r2 = &r as *mut i32;

	let i = Example{ uno: r.first };
	
	let x = Example{ uno: *r2 };
}