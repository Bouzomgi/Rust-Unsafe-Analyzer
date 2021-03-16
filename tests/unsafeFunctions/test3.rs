// Unsafe call to unsafe function outside of main function

fn main() {
	1;
}
	
fn tester() {
	newTester();
}

unsafe fn newTester() {
	1;
}

